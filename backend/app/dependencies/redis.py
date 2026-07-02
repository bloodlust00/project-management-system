from app.core.redis import RedisClient, redis_client


def get_redis() -> RedisClient:
    """Dependency injecting the application-wide Redis connection manager."""
    return redis_client
