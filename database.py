import os
from motor.motor_asyncio import AsyncIOMotorClient

# 1. Get Variable
MONGO_DETAILS = os.getenv("MONGO_DETAILS")

# 2. Debugging: Print what we found (Masked for security)
if MONGO_DETAILS:
    print(f"✅ LOADING DATABASE at: {MONGO_DETAILS[:20]}...")
else:
    print("🚨 CRITICAL ERROR: MONGO_DETAILS Variable is Missing!")

# 3. Fail-Safe: Do NOT use localhost. 
# If variable is missing, this will crash (which is better than silently failing on localhost)
if not MONGO_DETAILS:
    raise ValueError("MONGO_DETAILS environment variable is not set on Railway!")

# 4. Connect
client = AsyncIOMotorClient(MONGO_DETAILS)
db = client["shopify_video_db"]

# 5. Define Collections
shop_collection = db["shops"]
review_collection = db["reviews"]
social_collection = db["social_accounts"]
brand_collection = db["brand_settings"]
