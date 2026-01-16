import os
import redis
from rq import Worker, Queue, Connection

listen = ['default']

# 1. Get Redis URL from Environment
redis_url = os.getenv("REDIS_URL")

# 2. Safety Check (Print to Logs)
if not redis_url:
    print("🚨 CRITICAL ERROR: REDIS_URL environment variable is missing in Worker!")
    print("Worker is defaulting to localhost... THIS WILL FAIL on Railway.")
    # Attempting to use localhost anyway (which causes the crash you see)
    redis_url = "redis://localhost:6379"
else:
    print(f"✅ Worker connecting to Redis at: {redis_url[:20]}...")

# 3. Connect
conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        print("🚀 Worker Started... Listening for jobs.")
        worker = Worker(list(map(Queue, listen)))
        worker.work()
