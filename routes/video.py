import uuid
import json
import shutil
import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Form, File, UploadFile
from database import video_jobs_collection, q
from config import VIDEO_DIR
from tasks import process_video_job_task

router = APIRouter()

@router.post("/api/start-video-generation")
async def start_gen(
    image_urls: str = Form(...), product_title: str = Form(...), product_desc: str = Form(...),
    logo_url: Optional[str] = Form(None), voice_gender: str = Form("female"), duration: int = Form(15),
    script_tone: str = Form("Professional"), video_theme: str = Form("Modern"), music_file: UploadFile = File(None),
    shop_name: str = Form(...)
):
    job_id = str(uuid.uuid4())
    new_job = { "job_id": job_id, "status": "queued", "progress": 0, "created_at": datetime.utcnow(), "shop_name": shop_name, "title": product_title }
    await video_jobs_collection.insert_one(new_job)

    try: images_list = json.loads(image_urls)
    except: images_list = []
    
    custom_music_path = None
    if music_file:
        custom_music_path = os.path.join(VIDEO_DIR, f"bgm_{job_id}.mp3")
        with open(custom_music_path, "wb") as buffer:
            shutil.copyfileobj(music_file.file, buffer)
            
    q.enqueue(process_video_job_task, job_id, images_list, product_title, product_desc, logo_url, voice_gender, duration, script_tone, custom_music_path, video_theme, shop_name)
    
    return {"status": "queued", "job_id": job_id}

@router.get("/api/check-status/{job_id}")
async def check_status(job_id: str):
    job = await video_jobs_collection.find_one({"job_id": job_id})
    if not job: return {"status": "not_found"}
    return { "status": job.get("status"), "progress": job.get("progress", 0), "url": job.get("url"), "error": job.get("error") }