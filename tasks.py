import os
import google.generativeai as genai
from pymongo import MongoClient
from datetime import datetime
from utils import generate_video_from_images 

# Configuration from Railway
MONGO_DETAILS = os.getenv("MONGO_DETAILS")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
BASE_PUBLIC_URL = os.getenv("BASE_PUBLIC_URL")

# Worker uses MongoClient for stable synchronous updates
client = MongoClient(MONGO_DETAILS if MONGO_DETAILS else "mongodb://localhost:27017")
db = client.video_ai_db
video_jobs_collection = db.get_collection("video_jobs")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def update_progress_db(job_id, percent):
    video_jobs_collection.update_one(
        {"job_id": job_id},
        {"$set": {"progress": percent, "status": "processing", "updated_at": datetime.utcnow()}}
    )

def process_video_job_task(job_id, image_urls, title, desc, logo_url, voice_gender, 
                           duration, script_tone, custom_music_path, 
                           video_theme="Modern", shop_name=None):
    
    print(f"🎬 Worker Starting Job: {job_id}")
    try:
        update_progress_db(job_id, 10)

        # Generate Video (Ensure utils.py uses absolute paths for FFmpeg)
        filename, script_used = generate_video_from_images(
            image_urls, title, desc, logo_url, voice_gender, 
            duration, script_tone, custom_music_path, 
            lambda p: update_progress_db(job_id, p),
            shop_name=shop_name, 
            video_theme=video_theme
        )
        
        if filename:
            # Construct final public URL
            clean_url = (BASE_PUBLIC_URL or "").rstrip('/')
            video_url = f"{clean_url}/static/{filename}"
            
            video_jobs_collection.update_one(
                {"job_id": job_id},
                {"$set": {
                    "status": "done", 
                    "progress": 100, 
                    "url": video_url, 
                    "completed_at": datetime.utcnow()
                }}
            )
            print(f"✅ Video Generated Successfully: {filename}")
        else:
            raise Exception("Video generation returned no filename")

    except Exception as e:
        print(f"❌ Worker Fatal Error: {e}")
        video_jobs_collection.update_one(
            {"job_id": job_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )
