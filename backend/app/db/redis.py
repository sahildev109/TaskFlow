from typing import Optional
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import app_logger

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
        )
    return _redis_client


async def close_redis():
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
        app_logger.info("Redis connection closed")


# ── Token Blacklist ───────────────────────────────────────────────────────────
# Used for logout — invalidates JWTs before they expire

BLACKLIST_PREFIX = "blacklist:"
CACHE_PREFIX = "cache:"


async def blacklist_token(jti: str, expires_in: int):
    """Add token to Redis blacklist with TTL."""
    r = await get_redis()
    await r.setex(f"{BLACKLIST_PREFIX}{jti}", expires_in, "1")


async def is_token_blacklisted(jti: str) -> bool:
    r = await get_redis()
    return await r.exists(f"{BLACKLIST_PREFIX}{jti}") == 1


async def cache_set(key: str, value: str, ttl: int = 300):
    r = await get_redis()
    await r.setex(f"{CACHE_PREFIX}{key}", ttl, value)


async def cache_get(key: str) -> Optional[str]:
    r = await get_redis()
    return await r.get(f"{CACHE_PREFIX}{key}")


async def cache_delete(key: str):
    r = await get_redis()
    await r.delete(f"{CACHE_PREFIX}{key}")


async def cache_delete_pattern(pattern: str):
    r = await get_redis()
    keys = await r.keys(f"{CACHE_PREFIX}{pattern}")
    if keys:
        await r.delete(*keys)
