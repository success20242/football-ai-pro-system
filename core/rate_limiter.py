import asyncio
import time
from core.redis_client import redis_client

# =========================
# CONFIG
# =========================
DEFAULT_LIMIT = 8          # requests
DEFAULT_WINDOW = 1         # seconds


# =========================
# CORE RATE LIMITER
# =========================
async def acquire_slot(
    key: str = "global",
    limit: int = DEFAULT_LIMIT,
    window: int = DEFAULT_WINDOW,
    wait: bool = True
):
    """
    Distributed rate limiter using Redis

    key   → namespace (e.g. "football_api", "odds_api")
    limit → max requests per window
    window → time window (seconds)
    wait  → block until slot available
    """

    redis_key = f"rate:{key}:{int(time.time())}"

    while True:
        try:
            current = await redis_client.incr(redis_key)

            # set expiry only on first increment
            if current == 1:
                await redis_client.expire(redis_key, window)

            if current <= limit:
                return True

            # ❌ limit exceeded
            if not wait:
                return False

            # wait until next window
            await asyncio.sleep(0.05)

        except Exception:
            # fail-open (important in production)
            return True


# =========================
# MULTI-API LIMITERS
# =========================
async def football_api_limit():
    return await acquire_slot("football_api", limit=5, window=1)


async def odds_api_limit():
    return await acquire_slot("odds_api", limit=3, window=1)


async def team_stats_limit():
    return await acquire_slot("team_stats", limit=2, window=1)


# =========================
# BURST CONTROL (SMOOTHING)
# =========================
async def smooth_rate(delay: float = 0.1):
    """
    Adds micro-delay to avoid bursts
    """
    await asyncio.sleep(delay)


# =========================
# DECORATOR (🔥 CLEAN USAGE)
# =========================
def rate_limited(limit_func):
    """
    Usage:
    @rate_limited(football_api_limit)
    async def fetch(...):
        ...
    """
    def wrapper(func):
        async def inner(*args, **kwargs):
            await limit_func()
            return await func(*args, **kwargs)
        return inner
    return wrapper
