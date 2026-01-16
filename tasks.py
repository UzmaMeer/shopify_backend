import os
import google.generativeai as genai
from pymongo import MongoClient
from datetime import datetime
from utils import generate_video_from_images 

# Configuration from Railway Environment
MONGO_DETAILS = os.getenv("MONGO_DETAILS")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = os.getenv("BASE_PUBLIC_URL")

# Use MongoClient for stable synchronous updates in the worker
client = MongoClient(MONGO_DETAILS if MONGO_DETAILS else "mongodb://localhost:27017")
db = client.video_ai_db
video_jobs_collection = db.get_collection("video_jobs")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def update_job_progress(job_id, percent, status="processing"):
    video_jobs_collection.update_one(
        {"job_id": job_id},
        {"$set": {"progress": percent, "status": status, "updated_at": datetime.utcnow()}}
    )

def process_video_job_task(job_id, image_urls, title, desc, logo_url, voice_gender, duration, script_tone, custom_music_path, video_theme="Modern", shop_name=None):
    print(f"🎬 Starting video job: {job_id}")
    try:
        update_job_progress(job_id, 10)
        
        # Call the rendering logic in utils.py
        filename, script_used = generate_video_from_images(
            image_urls, title, desc, logo_url, voice_gender, 
            duration, script_tone, custom_music_path, 
            lambda p: update_job_progress(job_id, p),
            shop_name=shop_name, 
            video_theme=video_theme
        )

        if filename:
            video_url = f"{BASE_URL.rstrip('/')}/static/{filename}"
            video_jobs_collection.update_one(
                {"job_id": job_id},
                {"$set": {"status": "done", "progress": 100, "url": video_url, "completed_at": datetime.utcnow()}}
            )
            print(f"✅ Job completed: {filename}")
    except Exception as e:
        print(f"❌ Worker error: {str(e)}")
        update_job_progress(job_id, 0, status="failed")
