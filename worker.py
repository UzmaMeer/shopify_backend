import os
import redis
from rq import SimpleWorker, Queue

# 1. Listen to the 'default' queue
listen = ['default']

# 2. Setup Redis Connection
redis_url = 'redis://localhost:6379'
conn = redis.from_url(redis_url)

if __name__ == '__main__':
    print("👷 Windows Worker Started... Waiting for Video Jobs...")
    
    # 3. Create Worker manually
    queues = [Queue(name, connection=conn) for name in listen]
    worker = SimpleWorker(queues, connection=conn)
    
    worker.work()