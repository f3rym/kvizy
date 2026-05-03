import hashlib
import redis.asyncio as redis
from typing import Optional
from src.core.config import settings
from src.utils.logger import logger


class CacheService:
    """Service for caching Claude responses"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.ttl = 3600  # 1 hour

    async def connect(self):
        """Connect to Redis"""
        self.redis_client = await redis.from_url(settings.redis_url)
        logger.info("Cache service connected to Redis")

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()

    def _make_key(self, prompt: str, model: str = "default") -> str:
        """Generate cache key from prompt"""
        hash_obj = hashlib.md5(f"{model}:{prompt}".encode())
        return f"cache:claude:{hash_obj.hexdigest()}"

    async def get(self, prompt: str, model: str = "default") -> Optional[str]:
        """Get cached response"""
        if not self.redis_client:
            return None

        try:
            key = self._make_key(prompt, model)
            cached = await self.redis_client.get(key)

            if cached:
                logger.info(f"Cache hit for prompt (key={key})")
                return cached.decode('utf-8')

            logger.info(f"Cache miss for prompt (key={key})")
            return None

        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None

    async def set(self, prompt: str, response: str, model: str = "default"):
        """Cache response"""
        if not self.redis_client:
            return

        try:
            key = self._make_key(prompt, model)
            await self.redis_client.setex(key, self.ttl, response.encode('utf-8'))
            logger.info(f"Cached response (key={key}, ttl={self.ttl}s)")

        except Exception as e:
            logger.error(f"Error setting cache: {e}")

    async def clear_user_cache(self, user_id: int):
        """Clear all cache for user (not implemented - would need user-specific keys)"""
        pass

    async def clear_all(self):
        """Clear all cache (admin only)"""
        if not self.redis_client:
            return

        try:
            keys = await self.redis_client.keys("cache:claude:*")
            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")


# Global cache service instance
cache_service = CacheService()
