import os
import requests
import google.generativeai as genai
from pymongo import MongoClient
from datetime import datetime
# Ensure your utils.py contains generate_video_from_images
from utils import generate_video_from_images 

# --- CONFIGURATION ---
# Railway Environment Variables se URL uthayen
MONGO_DETAILS = os.getenv("MONGO_DETAILS")
if not MONGO_DETAILS:
    print("🚨 ERROR: MONGO_DETAILS not found. Falling back to localhost (Will fail on Railway)")
    MONGO_DETAILS = "mongodb://localhost:27017"

client = MongoClient(MONGO_DETAILS)
db = client.video_ai_db
# Collection ka naam aapki database.py file ke mutabiq
video_jobs_collection = db.get_collection("video_jobs")

# API Keys Railway Variables se
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

BASE_PUBLIC_URL = os.getenv("BASE_PUBLIC_URL")

# --- HELPER FUNCTIONS ---
def generate_viral_caption(title, desc):
    try:
        # Latest supported model for Railway compatibility
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = (f"Write a short, viral Instagram/TikTok caption for '{title}'. "
                  f"Include 3-4 trending hashtags. Under 2 sentences. No quotes.")
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        print(f"⚠️ Caption AI Error: {e}")
        return f"Check out {title}! #Trending #Fashion"

# --- THE MAIN WORKER FUNCTION ---
def process_video_job_task(job_id, image_urls, title, desc, logo_url, voice_gender, 
                           duration, script_tone, custom_music_path, 
                           video_theme="Modern", shop_name=None):
    
    print(f"🛠️ Worker Starting Job: {job_id}")

    def update_progress_db(percent):
        video_jobs_collection.update_one(
            {"job_id": job_id},
            {"$set": {
                "progress": percent, 
                "status": "processing", 
                "updated_at": datetime.utcnow()
            }}
        )

    try:
        # Initial DB Status
        update_progress_db(10)

        # 2. Call Utils to Generate Video
        filename, script_used = generate_video_from_images(
            image_urls, title, desc, logo_url, voice_gender, 
            duration, script_tone, custom_music_path, 
            update_progress_db,  # Callback for progress tracking
            shop_name=shop_name, 
            video_theme=video_theme
        )
        
        if filename:
            update_progress_db(98)
            
            smart_caption = generate_viral_caption(title, desc)
            
            # Clean public URL
            clean_base_url = (BASE_PUBLIC_URL or "").rstrip('/')
            video_url = f"{clean_base_url}/static/{filename}"
            print(f"✅ Worker Finished: {filename}")
            
            video_jobs_collection.update_one(
                {"job_id": job_id},
                {
                    "$set": {
                        "status": "done", 
                        "progress": 100, 
                        "url": video_url, 
                        "filename": filename, 
                        "caption": smart_caption,
                        "completed_at": datetime.utcnow()
                    }
                }
            )
        else:
            video_jobs_collection.update_one(
                {"job_id": job_id},
                {"$set": {"status": "failed", "error": "Utils returned None"}}
            )

    except Exception as e:
        print(f"❌ Worker Error: {e}")
        video_jobs_collection.update_one(
            {"job_id": job_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )
