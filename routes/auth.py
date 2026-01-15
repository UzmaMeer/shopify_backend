import requests
from datetime import datetime
from urllib.parse import urlencode
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from authlib.integrations.starlette_client import OAuth
from database import shop_collection, social_collection
from config import *

router = APIRouter()
oauth = OAuth()

# OAuth Config
oauth.register(
    name='instagram', client_id=META_CLIENT_ID, client_secret=META_CLIENT_SECRET,
    access_token_url='https://graph.facebook.com/v21.0/oauth/access_token',
    authorize_url='https://www.facebook.com/v21.0/dialog/oauth',
    api_base_url='https://graph.facebook.com/', client_kwargs={'scope': 'public_profile,pages_show_list,pages_read_engagement,pages_manage_posts,instagram_basic,instagram_content_publish,business_management'},
)
oauth.register(
    name='tiktok', client_id=TIKTOK_CLIENT_KEY, client_secret=TIKTOK_CLIENT_SECRET,
    access_token_url='https://open.tiktokapis.com/v2/oauth/token/',
    authorize_url='https://www.tiktok.com/v2/auth/authorize/',
    api_base_url='https://open.tiktokapis.com/v2/',
    client_kwargs={'scope': 'user.info.basic,video.upload'}, authorize_params={'client_key': TIKTOK_CLIENT_KEY} 
)

@router.get("/api/auth")
def shopify_auth(shop: str):
    if not shop: return {"error": "Missing shop"}
    scopes = "read_products,write_products,write_script_tags"
    redirect_uri = f"{BASE_PUBLIC_URL}/api/auth/callback"
    install_url = f"https://{shop}/admin/oauth/authorize?client_id={SHOPIFY_API_KEY}&scope={scopes}&redirect_uri={redirect_uri}"
    return RedirectResponse(install_url)

@router.get("/api/auth/callback")
async def shopify_callback(shop: str, code: str):
    url = f"https://{shop}/admin/oauth/access_token"
    payload = {"client_id": SHOPIFY_API_KEY, "client_secret": SHOPIFY_API_SECRET, "code": code}
    try:
        resp = requests.post(url, json=payload)
        data = resp.json()
        if "access_token" in data:
            await shop_collection.update_one({"shop": shop}, {"$set": {"access_token": data["access_token"], "updated_at": datetime.utcnow()}}, upsert=True)
    except Exception as e: print(f"❌ Auth Error: {e}")
    return RedirectResponse(f"https://{shop}/admin/apps/{SHOPIFY_API_KEY}")

@router.get("/login/{platform}")
async def social_login(platform: str, request: Request):
    redirect_uri = f"{BASE_PUBLIC_URL}/auth/callback/{platform}"
    client = oauth.create_client(platform)
    request.scope["scheme"] = "https"
    if platform.lower() == "tiktok":
        base_url = "https://www.tiktok.com/v2/auth/authorize/"
        params = {"client_key": TIKTOK_CLIENT_KEY, "response_type": "code", "scope": "user.info.basic,video.upload", "redirect_uri": redirect_uri, "state": "somerandomstring"}
        return RedirectResponse(f"{base_url}?{urlencode(params)}")
    return await client.authorize_redirect(request, redirect_uri)

@router.get("/auth/callback/{platform}")
async def auth_callback(platform: str, request: Request):
    request.scope["scheme"] = "https"
    try:
        client = oauth.create_client(platform)
        token = await client.authorize_access_token(request)
        user_id = "tiktok_user" if platform == "tiktok" else (await client.get('me', token=token)).json().get('id')
        await social_collection.update_one({"platform": platform, "platform_user_id": user_id}, {"$set": {"token_data": token}}, upsert=True)
        return HTMLResponse("<script>window.close();</script><h1>Connected!</h1>")
    except Exception as e: return HTMLResponse(f"<h1>Error: {str(e)}</h1>")