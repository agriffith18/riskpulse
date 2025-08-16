import redis.asyncio as redis
from .settings import settings

# Simple Redis client - no wrapper needed!
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)