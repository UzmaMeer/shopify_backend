import os
import redis
from rq import Queue
from motor.motor_asyncio import AsyncIOMotorClient

# Connect using Railway Environment Variables
MONGO_DETAILS = os.getenv("MONGO_DETAILS")
if not MONGO_DETAILS:
    # Fallback only for local testing
    MONGO_DETAILS = "mongodb://localhost:27017"

client_db = AsyncIOMotorClient(MONGO_DETAILS)
database = client_db.video_ai_db

# Collections - Names fixed to match your route imports
video_jobs_collection = database.get_collection("video_jobs")
social_collection = database.get_collection("social_accounts")
shop_collection = database.get_collection("shopify_stores")
brand_collection = database.get_collection("brand_settings")

# Redis Queue Setup
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_conn = redis.from_url(REDIS_URL)
q = Queue(connection=redis_conn)
