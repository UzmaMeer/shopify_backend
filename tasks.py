import os
import requests
import google.generativeai as genai
from pymongo import MongoClient
from datetime import datetime
from database import video_jobs_collection, database

# --- CONFIGURATION ---
# Database Connection (Worker ke liye PyMongo use karein, Motor nahi)
MONGO_DETAILS = "mongodb://localhost:27017"
client = MongoClient(MONGO_DETAILS)
db = client.video_ai_db
video_jobs_collection = db.get_collection("video_jobs")

# API Keys (Wohi same keys jo main.py mein thin)
genai.configure(api_key="AIzaSyDlFXPnGyBv8Rq4jZZP_aMQNM16UaQa5Dc")
BASE_PUBLIC_URL = "https://snakiest-edward-autochthonously.ngrok-free.dev"

# --- HELPER FUNCTIONS ---
def generate_viral_caption(title, desc):
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = (f"Write a short, viral Instagram/TikTok caption for '{title}'. Include 3-4 trending hashtags. Under 2 sentences. No quotes.")
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except:
        return f"Check out {title}! #Trending #Fashion"

# --- THE MAIN WORKER FUNCTION ---
def process_video_job_task(job_id, image_urls, title, desc, logo_url, voice_gender, duration, script_tone, custom_music_path, video_theme="Modern", shop_name=None):
    """
    Ye function ab Worker Process mein chalega.
    Isliye ye Status ko Memory (Dict) ki bajaye seedha MongoDB mein update karega.
    """
    print(f"🛠️ Worker Starting Job: {job_id}")

    # 1. Helper to update DB progress
    def update_progress_db(percent):
        video_jobs_collection.update_one(
            {"job_id": job_id},
            {"$set": {"progress": percent, "status": "processing", "updated_at": datetime.utcnow()}}
        )

    try:
        # Initial DB Status
        update_progress_db(10)

        # 2. Call Utils to Generate Video
        filename, script_used = generate_video_from_images(
            image_urls, title, desc, logo_url, voice_gender, 
            duration, script_tone, custom_music_path, 
            update_progress_db,  # Pass DB updater instead of memory updater
            shop_name=shop_name, 
            video_theme=video_theme
        )
        
        if filename:
            # 3. Update to 98% (Captioning Time)
            update_progress_db(98)
            
            # 4. Generate Caption
            smart_caption = generate_viral_caption(title, desc)
            
            video_url = f"{BASE_PUBLIC_URL}/static/{filename}"
            print(f"✅ Worker Finished: {filename}")
            
            # 5. Final Success Update in DB
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