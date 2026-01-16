import os
import redis
from rq import Queue
from motor.motor_asyncio import AsyncIOMotorClient

# 1. Database Setup
# We use the MONGO_DETAILS variable from your Railway settings
MONGO_DETAILS = os.getenv("MONGO_DETAILS")

if not MONGO_DETAILS:
    print("🚨 CRITICAL ERROR: MONGO_DETAILS variable not found!")
    # Fallback to localhost for safety, but it will likely fail on Railway
    MONGO_DETAILS = "mongodb://localhost:27017"

client_db = AsyncIOMotorClient(MONGO_DETAILS)
database = client_db.video_ai_db

# 2. Collections (Crucial: Added 'video_jobs_collection')
video_jobs_collection = database.get_collection("video_jobs")  # 👈 This was missing!
social_collection = database.get_collection("social_accounts")
shop_collection = database.get_collection("shopify_stores")
brand_collection = database.get_collection("brand_settings")
publish_collection = database.get_collection("publish_jobs")
review_collection = database.get_collection("user_reviews")

# 3. Redis Queue Setup
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_conn = redis.from_url(REDIS_URL)
# Exporting 'q' for the worker and routes to use
q = Queue(connection=redis_conn)
