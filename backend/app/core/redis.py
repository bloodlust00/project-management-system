import json
from typing import Any, Optional

import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import logger


class RedisClient:
    def __init__(self):
        self.client: Optional[aioredis.Redis] = None

    def connect(self):
        """Initializes connection to Redis instance."""
        try:
            self.client = aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=5.0)
            logger.info("Successfully connected to Redis.")
        except Exception as e:
            logger.error(f"Failed to connect to Redis at {settings.REDIS_URL}: {e}")
            self.client = None

    async def disconnect(self):
        """Closes the Redis connection connection pool."""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed.")

    async def is_active(self) -> bool:
        """Check if Redis connection is active."""
        if not self.client:
            return False
        try:
            return await self.client.ping()
        except Exception:
            return False

    async def blacklist_token(self, token_jti: str, expires_in_seconds: int) -> bool:
        """Blacklists a JWT token jti/signature until expiration."""
        if not self.client:
            return False
        try:
            await self.client.setex(f"blacklist:{token_jti}", expires_in_seconds, "true")
            return True
        except Exception as e:
            logger.error(f"Error blacklisting token in Redis: {e}")
            return False

    async def is_token_blacklisted(self, token_jti: str) -> bool:
        """Checks if a JWT token has been blacklisted."""
        if not self.client:
            return False
        try:
            result = await self.client.get(f"blacklist:{token_jti}")
            return result is not None
        except Exception as e:
            logger.error(f"Error checking token blacklist in Redis: {e}")
            return False

    async def get_cache(self, key: str) -> Optional[Any]:
        """Gets serializable cached value by key."""
        if not self.client:
            return None
        try:
            val = await self.client.get(key)
            if val:
                return json.loads(val)
            return None
        except Exception as e:
            logger.error(f"Failed to read from cache key {key}: {e}")
            return None

    async def set_cache(self, key: str, value: Any, expire_seconds: int = 300) -> bool:
        """Saves values into cache with serialization and expiration times."""
        if not self.client:
            return False
        try:
            serialized = json.dumps(value)
            await self.client.setex(key, expire_seconds, serialized)
            return True
        except Exception as e:
            logger.error(f"Failed to write to cache key {key}: {e}")
            return False

    async def delete_cache(self, key: str) -> bool:
        """Deletes specific key from the cache."""
        if not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False

    async def delete_by_pattern(self, pattern: str) -> bool:
        """Deletes all cache keys matching specific pattern (e.g. 'projects:*') using non-blocking scan_iter."""
        if not self.client:
            return False
        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await self.client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys matching pattern: {pattern}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete keys by pattern {pattern}: {e}")
            return False


redis_client = RedisClient()
# Connect to Redis immediately on module loading for non-async parts if needed
redis_client.connect()
