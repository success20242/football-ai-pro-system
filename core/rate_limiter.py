import time
from core.redis_client import redis_client

LIMIT = 8  # requests per second
WINDOW = 1


async def acquire_slot():
    now = int(time.time())
    key = f"rate:{now}"

    current = await redis_client.incr(key)
    await redis_client.expire(key, WINDOW)

    return current <= LIMIT
