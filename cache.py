import redis
import os

redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379, db=0)