import os
import redis
from rq import Worker, Queue
# ❌ Removed 'Connection' from imports to fix the crash

listen = ['default']

# 1. Get Redis URL from Environment
redis_url = os.getenv("REDIS_URL")

if not redis_url:
    print("🚨 REDIS_URL not found! Defaulting to localhost (This will fail on Railway)")
    redis_url = "redis://localhost:6379"

# 2. Connect to Redis
conn = redis.from_url(redis_url)

if __name__ == '__main__':
    print(f"🚀 Worker starting... Connecting to Redis at {redis_url[:20]}...")
    
    # 3. Create Queue with explicit connection
    q = Queue('default', connection=conn)
    
    # 4. Start Worker with explicit connection (No 'with Connection' block needed)
    worker = Worker([q], connection=conn)
    worker.work()
