import requests
from datetime import datetime
from fastapi import APIRouter, Query
from database import shop_collection, review_collection, social_collection, brand_collection
from models import ReviewRequest, BrandSettingsRequest

router = APIRouter()

@router.get("/api/products")
async def get_products(shop: str = None, search: str = Query(None)):
    if not shop: return {"products": []}
    store_data = await shop_collection.find_one({"shop": shop})
    if not store_data: return {"error": "auth_needed"}
    
    token = store_data["access_token"]
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
    url = f"https://{shop}/admin/api/2024-01/products.json"
    params = {"limit": 50}
    try:
        r = requests.get(url, headers=headers, params=params)
        all_products = r.json().get("products", [])
        if search:
            return {"products": [p for p in all_products if search.lower() in p.get('title', '').lower()]}
        return {"products": all_products}
    except Exception as e: return {"products": [], "error": str(e)}

@router.post("/api/reviews")
async def add_review(review: ReviewRequest):
    new_review = review.dict()
    new_review["created_at"] = datetime.utcnow()
    new_review["is_approved"] = True 
    await review_collection.insert_one(new_review)
    return {"status": "success"}

@router.get("/api/reviews")
async def get_reviews():
    real_reviews = []
    async for doc in review_collection.find({"is_approved": True}).limit(10):
        doc["_id"] = str(doc["_id"])
        real_reviews.append(doc)
    static_reviews = [
        {"name": "Sarah K.", "rating": 5, "comment": "Sales increased by 30%!", "designation": "Store Owner"},
        {"name": "Ali R.", "rating": 5, "comment": "Best tool for Shopify.", "designation": "Gadget Shop"}
    ]
    return {"reviews": static_reviews + real_reviews}

@router.get("/api/social-accounts")
async def get_accounts():
    accounts = []
    async for doc in social_collection.find({}):
        accounts.append({"id": str(doc["_id"]), "platform": doc.get("platform")})
    return {"status": "success", "accounts": accounts}

@router.post("/api/save-brand-settings")
async def save_brand_settings(settings: BrandSettingsRequest):
    await brand_collection.update_one({"shop": settings.shop}, {"$set": settings.dict()}, upsert=True)
    return {"status": "success"}

@router.get("/api/get-brand-settings")
async def get_brand_settings(shop: str):
    data = await brand_collection.find_one({"shop": shop})
    if data: data.pop("_id", None)
    return data or {}