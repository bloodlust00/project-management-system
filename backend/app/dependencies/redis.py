from app.core.redis import redis_client, RedisClient

def get_redis() -> RedisClient:
    """Dependency injecting the application-wide Redis connection manager."""
    return redis_client
