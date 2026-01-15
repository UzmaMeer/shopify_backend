import asyncio
import requests
from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse
from database import publish_collection, social_collection, video_jobs_collection
from models import PublishRequest
from config import BASE_PUBLIC_URL, IG_USER_ID

router = APIRouter()

# --- Helpers ---
async def perform_instagram_upload(access_token, video_url, caption):
    try:
        url_create = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media"
        payload = { "video_url": video_url, "media_type": "REELS", "caption": caption, "access_token": access_token }
        r = requests.post(url_create, data=payload)
        data = r.json()
        if "id" not in data: return False, f"Container Error: {data.get('error', {}).get('message')}"
        creation_id = data["id"]
        status_url = f"https://graph.facebook.com/v21.0/{creation_id}"
        
        for i in range(20): 
            await asyncio.sleep(3)
            check = requests.get(status_url, params={"fields": "status_code,status", "access_token": access_token}).json()
            if check.get("status_code") == "FINISHED": break
            if check.get("status_code") == "ERROR": return False, f"Processing Error: {check}"
        
        publish_url = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media_publish"
        r_pub = requests.post(publish_url, data={"creation_id": creation_id, "access_token": access_token})
        pub_data = r_pub.json()
        return ("id" in pub_data), pub_data.get("id") or pub_data.get('error', {}).get('message')
    except Exception as e: return False, str(e)

async def perform_facebook_upload(access_token, video_url, caption):
    try:
        pages_url = "https://graph.facebook.com/v21.0/me/accounts"
        resp = requests.get(pages_url, params={"access_token": access_token}).json()
        if not resp.get("data"): return False, "No Facebook Pages found."
        page = resp["data"][0]
        post_url = f"https://graph.facebook.com/v21.0/{page['id']}/videos"
        r = requests.post(post_url, params={"file_url": video_url, "description": caption, "access_token": page['access_token']})
        res = r.json()
        return ("id" in res), res.get("id") or res.get('error', {}).get('message')
    except Exception as e: return False, str(e)

async def background_publish_worker(publish_job_id: str, filename: str, accounts: list, caption: str):
    print(f"🚀 Starting Background Publish for Job {publish_job_id}")
    video_url = f"{BASE_PUBLIC_URL}/static/{filename}"
    results = {}
    overall_status = "succeeded"
    
    await publish_collection.update_one({"_id": ObjectId(publish_job_id)}, {"$set": {"status": "processing", "started_at": datetime.utcnow()}})
    
    for platform in accounts:
        try:
            acc = await social_collection.find_one({"platform": platform})
            if not acc:
                results[platform] = {"status": "failed", "error": "Account not connected"}
                continue
            
            token = acc['token_data']['access_token']
            success, result_msg = False, ""
            
            if platform == "instagram": success, result_msg = await perform_instagram_upload(token, video_url, caption)
            elif platform == "facebook": success, result_msg = await perform_facebook_upload(token, video_url, caption)
            
            results[platform] = {"status": "success", "post_id": result_msg} if success else {"status": "failed", "error": result_msg}
            if not success: overall_status = "partial_failure"
        except Exception as e:
            results[platform] = {"status": "failed", "error": str(e)}
            overall_status = "partial_failure"

    if all(r["status"] == "failed" for r in results.values()): overall_status = "failed"
    await publish_collection.update_one({"_id": ObjectId(publish_job_id)}, {"$set": {"status": overall_status, "platform_results": results, "completed_at": datetime.utcnow()}})

# --- Routes ---
@router.post("/api/queue-publish")
async def queue_publish(request: PublishRequest, background_tasks: BackgroundTasks):
    filename = request.video_filename
    caption = request.caption_override
    
    if not filename and request.render_job_id:
        job = await video_jobs_collection.find_one({"job_id": request.render_job_id})
        if job and job.get("filename"):
            filename = job["filename"]
            if not caption: caption = job.get("caption", "")

    if not filename:
        return JSONResponse(status_code=400, content={"error": "No video found. Please provide render_job_id or filename."})

    new_job = await publish_collection.insert_one({
        "render_job_id": request.render_job_id, "video_filename": filename, "caption": caption,
        "platforms": request.accounts, "status": "queued", "created_at": datetime.utcnow()
    })
    background_tasks.add_task(background_publish_worker, str(new_job.inserted_id), filename, request.accounts, caption)
    return {"status": "queued", "publish_job_id": str(new_job.inserted_id)}

@router.get("/api/publish-status/{publish_job_id}")
async def get_publish_status(publish_job_id: str):
    try:
        job = await publish_collection.find_one({"_id": ObjectId(publish_job_id)})
        if job: job["_id"] = str(job["_id"]); return job
        return {"error": "Job not found"}
    except: return {"error": "Invalid ID"}