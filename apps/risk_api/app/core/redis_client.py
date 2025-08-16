import redis.asyncio as redis
from .settings import settings

# Create Redis client with proper connection pool management
redis_client = redis.from_url(
    settings.REDIS_URL, 
    decode_responses=True,
    max_connections=20,  # Limit connection pool size
    socket_keepalive=True,
    socket_keepalive_options={},
    retry_on_timeout=True
)