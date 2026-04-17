from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import settings

_redis: aioredis.Redis | None = None


async def init_redis() -> aioredis.Redis:
    """Initialize and return the singleton Redis connection."""
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def close_redis() -> None:
    """Close the Redis connection."""
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """FastAPI dependency that provides an async Redis connection."""
    redis = await init_redis()
    try:
        yield redis
    finally:
        # Do not close here; the lifespan handler manages the connection lifecycle.
        pass
