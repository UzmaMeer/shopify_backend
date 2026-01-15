import redis
from rq import Queue
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB Setup
MONGO_DETAILS = "mongodb://localhost:27017"
client_db = AsyncIOMotorClient(MONGO_DETAILS)
database = client_db.video_ai_db

# Collections
video_jobs_collection = database.get_collection("video_jobs")
social_collection = database.get_collection("social_accounts")
shop_collection = database.get_collection("shopify_stores")
brand_collection = database.get_collection("brand_settings")
publish_collection = database.get_collection("publish_jobs")
review_collection = database.get_collection("user_reviews")

# Redis Queue Setup
redis_conn = redis.Redis()
q = Queue(connection=redis_conn)