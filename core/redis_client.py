import os
import asyncio
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)


# =========================
# SINGLETON POOL
# =========================
_pool = None
_client = None


def get_redis_pool():
    global _pool

    if _pool is None:
        _pool = redis.ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            max_connections=50,
        )

    return _pool


def get_redis():
    global _client

    if _client is None:
        _client = redis.Redis(connection_pool=get_redis_pool())

    return _client


redis_client = get_redis()


# =========================
# HEALTH CHECK
# =========================
async def check_redis():
    try:
        return await redis_client.ping()
    except Exception as e:
        print("❌ Redis connection failed:", e)
        return False


# =========================
# SAFE CALL WRAPPER (FIXED)
# =========================
async def safe_redis_call(func, *args, retries=3, delay=0.2, **kwargs):
    """
    FIXED:
    - supports kwargs
    - retries with exponential backoff
    - safer Redis recovery behavior
    """

    for attempt in range(retries):
        try:
            return await func(*args, **kwargs)

        except Exception as e:
            if attempt == retries - 1:
                print(f"❌ Redis failed permanently: {e}")
                return None

            await asyncio.sleep(delay * (2 ** attempt))


# =========================
# RECONNECT HELPERS
# =========================
async def reconnect():
    """
    Forces redis reconnect if connection breaks
    """
    global _client, _pool

    try:
        if _client:
            await _client.close()

        _pool = None
        _client = get_redis()

        await _client.ping()
        return True

    except Exception as e:
        print("❌ Redis reconnect failed:", e)
        return False


# =========================
# SHUTDOWN
# =========================
async def close_redis():
    global _pool, _client

    try:
        if _client:
            await _client.close()

        if _pool:
            await _pool.disconnect()

        print("✅ Redis pool closed")

    except Exception as e:
        print("⚠️ Redis shutdown error:", e)
