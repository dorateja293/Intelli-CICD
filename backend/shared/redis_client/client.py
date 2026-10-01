"""
Redis Client Module

Provides async Redis client with connection pooling.
"""

import json
from functools import lru_cache
from typing import Any, Optional

import redis.asyncio as redis
import structlog

from config.settings import get_settings

logger = structlog.get_logger()
settings = get_settings()


@lru_cache
def get_redis_pool() -> redis.ConnectionPool:
    """Get cached Redis connection pool."""
    return redis.ConnectionPool.from_url(
        settings.redis.url,
        max_connections=settings.redis.max_connections,
        decode_responses=True,
    )


def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    return redis.Redis(connection_pool=get_redis_pool())


async def close_redis() -> None:
    """Close Redis connection pool."""
    pool = get_redis_pool()
    await pool.disconnect()


class RedisClient:
    """Async Redis client wrapper with common utilities."""

    def __init__(self):
        self.redis = get_redis()

    # ================================
    # Basic Operations
    # ================================

    async def get(self, key: str) -> Optional[str]:
        """Get a string value."""
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.debug("Redis get failed, falling back", key=key, error=str(e))
            return None

    async def set(
        self,
        key: str,
        value: str,
        ex: Optional[int] = None,
        nx: bool = False,
    ) -> Optional[bool]:
        """Set a string value with optional expiry and NX flag."""
        try:
            return await self.redis.set(key, value, ex=ex, nx=nx)
        except Exception as e:
            logger.debug("Redis set failed, continuing without cache", key=key, error=str(e))
            return None

    async def delete(self, *keys: str) -> int:
        """Delete keys."""
        try:
            return await self.redis.delete(*keys)
        except Exception as e:
            logger.debug("Redis delete failed", error=str(e))
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.debug("Redis exists failed", error=str(e))
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration."""
        try:
            return await self.redis.expire(key, seconds)
        except Exception as e:
            logger.debug("Redis expire failed", error=str(e))
            return False

    # ================================
    # Health Check
    # ================================

    async def ping(self) -> bool:
        """Ping Redis server."""
        try:
            return await self.redis.ping()
        except Exception:
            return False

    # ================================
    # Idempotency Check
    # ================================

    async def check_idempotency(self, key: str, ttl: int = 300) -> bool:
        """
        Check if operation is duplicate using NX set.
        Returns True if this is the first occurrence.
        """
        result = await self.redis.set(f"idem:{key}", "1", nx=True, ex=ttl)
        return result is not None

    # ================================
    # Rate Limiting (Sliding Window)
    # ================================

    async def check_rate_limit(
        self,
        key: str,
        limit: int = 1000,
        window: int = 60,
    ) -> tuple[bool, int]:
        """
        Check rate limit using sliding window.
        Returns (allowed, current_count).
        """
        import time

        now = time.time()
        full_key = f"rl:{key}"

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(full_key, 0, now - window)
        pipe.zadd(full_key, {str(now): now})
        pipe.zcard(full_key)
        pipe.expire(full_key, window)
        results = await pipe.execute()

        count = results[2]
        return count <= limit, count

    # ================================
    # Redis Streams (Job Queue)
    # ================================

    async def xgroup_create(
        self,
        stream: str,
        group: str,
        mkstream: bool = True,
    ) -> None:
        """Create consumer group, ignore if exists."""
        try:
            await self.redis.xgroup_create(stream, group, id="0", mkstream=mkstream)
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def xadd(
        self,
        stream: str,
        fields: dict[str, Any],
        maxlen: int = 10000,
    ) -> str:
        """Add message to stream."""
        # Serialize dict values to strings
        serialized = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in fields.items()}
        return await self.redis.xadd(stream, serialized, maxlen=maxlen)

    async def xreadgroup(
        self,
        group: str,
        consumer: str,
        streams: dict[str, str],
        count: int = 1,
        block: int = 5000,
    ) -> list:
        """Read from consumer group."""
        return await self.redis.xreadgroup(group, consumer, streams, count=count, block=block)

    async def xack(self, stream: str, group: str, *ids: str) -> int:
        """Acknowledge messages."""
        return await self.redis.xack(stream, group, *ids)

    async def xpending_range(
        self,
        stream: str,
        group: str,
        min_id: str = "-",
        max_id: str = "+",
        count: int = 10,
        idle: Optional[int] = None,
    ) -> list:
        """Get pending entries."""
        return await self.redis.xpending_range(stream, group, min_id, max_id, count, idle=idle)

    async def xclaim(
        self,
        stream: str,
        group: str,
        consumer: str,
        min_idle_time: int,
        message_ids: list[str],
    ) -> list:
        """Claim pending messages."""
        return await self.redis.xclaim(stream, group, consumer, min_idle_time, message_ids)

    # ================================
    # Pub/Sub (for SSE)
    # ================================

    async def publish(self, channel: str, message: str) -> int:
        """Publish message to channel."""
        return await self.redis.publish(channel, message)

    def pubsub(self) -> redis.client.PubSub:
        """Get pubsub instance."""
        return self.redis.pubsub()

    # ================================
    # List Operations (Log Cache)
    # ================================

    async def rpush(self, key: str, *values: str) -> int:
        """Append to list."""
        return await self.redis.rpush(key, *values)

    async def ltrim(self, key: str, start: int, stop: int) -> bool:
        """Trim list to specified range."""
        return await self.redis.ltrim(key, start, stop)

    async def lrange(self, key: str, start: int, stop: int) -> list[str]:
        """Get list range."""
        return await self.redis.lrange(key, start, stop)

    # ================================
    # Health Check
    # ================================

    async def ping(self) -> bool:
        """Ping Redis server."""
        return await self.redis.ping()


# Singleton instance
_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """Get Redis client singleton."""
    global _client
    if _client is None:
        _client = RedisClient()
    return _client
