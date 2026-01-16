import os
import redis
from rq import Worker, Queue
# ❌ Fixed: Removed 'Connection' import causing the crash

listen = ['default']

# 1. Get Redis URL
redis_url = os.getenv("REDIS_URL")

if not redis_url:
    print("🚨 WORKER ERROR: REDIS_URL is missing!")
    # Just for safety, though it will likely fail on Railway if missing
    redis_url = "redis://localhost:6379"

# 2. Connect
conn = redis.from_url(redis_url)

if __name__ == '__main__':
    print(f"🚀 Worker Started. Connecting to Redis...")
    
    # 3. Create Queue with explicit connection
    q = Queue('default', connection=conn)
    
    # 4. Start Worker (Explicit connection, no 'with' block)
    worker = Worker([q], connection=conn)
    worker.work()
