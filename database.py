import os
import redis
from rq import Queue
from motor.motor_asyncio import AsyncIOMotorClient

# Use verified Railway variable
MONGO_DETAILS = os.getenv("MONGO_DETAILS")
if not MONGO_DETAILS:
    MONGO_DETAILS = "mongodb://localhost:27017"

client_db = AsyncIOMotorClient(MONGO_DETAILS)
database = client_db.video_ai_db

# Export all collections needed by your routes
video_jobs_collection = database.get_collection("video_jobs")
social_collection = database.get_collection("social_accounts")
shop_collection = database.get_collection("shopify_stores")
brand_collection = database.get_collection("brand_settings")
publish_collection = database.get_collection("publish_jobs") # Added this
review_collection = database.get_collection("user_reviews") # Added this

# Redis Queue
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_conn = redis.from_url(REDIS_URL)
q = Queue(connection=redis_conn)
