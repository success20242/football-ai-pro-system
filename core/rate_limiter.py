import asyncio
import time
import random
from functools import wraps
from core.redis_client import redis_client

# =========================
# CONFIG
# =========================
DEFAULT_LIMIT = 8
DEFAULT_WINDOW = 1  # seconds


# =========================
# SLIDING WINDOW RATE LIMITER
# =========================
async def acquire_slot(
    key: str = "global",
    limit: int = DEFAULT_LIMIT,
    window: int = DEFAULT_WINDOW,
    wait: bool = True
):
    """
    FIXED:
    - uses sliding window bucket (not per-second key explosion)
    - stable under concurrency
    """

    bucket_key = f"rate:{key}"

    while True:
        try:
            now = int(time.time())

            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(bucket_key, 0, now - window)
            pipe.zcard(bucket_key)
            _, count = await pipe.execute()

            if count < limit:
                await redis_client.zadd(bucket_key, {str(time.time()): time.time()})
                await redis_client.expire(bucket_key, window + 1)
                return True

            if not wait:
                return False

            # jitter prevents synchronized retry storms
            await asyncio.sleep(0.05 + random.random() * 0.05)

        except Exception:
            # fail-open (critical systems stability)
            return True


# =========================
# API LIMITERS
# =========================
async def football_api_limit():
    return await acquire_slot("football_api", limit=5, window=1)


async def odds_api_limit():
    return await acquire_slot("odds_api", limit=3, window=1)


async def team_stats_limit():
    return await acquire_slot("team_stats", limit=2, window=1)


# =========================
# SMOOTHING (ANTI-BURST)
# =========================
async def smooth_rate(delay: float = 0.1):
    await asyncio.sleep(delay)


# =========================
# FIXED DECORATOR
# =========================
def rate_limited(limit_func):
    """
    Safe async decorator with metadata preservation
    """

    def wrapper(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            await limit_func()
            return await func(*args, **kwargs)

        return inner

    return wrapper
