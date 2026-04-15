import os
import asyncio
import redis.asyncio as redis
from dotenv import load_dotenv

# =========================
# LOAD ENV
# =========================
load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)


# =========================
# CONNECTION POOL (IMPORTANT)
# =========================
_pool = None


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
            max_connections=20,  # 🔥 prevents overload
        )

    return _pool


# =========================
# CLIENT FACTORY
# =========================
def get_redis():
    return redis.Redis(connection_pool=get_redis_pool())


# singleton (safe reuse)
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
# SAFE EXECUTOR (AUTO RETRY)
# =========================
async def safe_redis_call(func, *args, retries=3, delay=0.2):
    """
    Wrap Redis calls with retry logic
    """
    for attempt in range(retries):
        try:
            return await func(*args)

        except Exception as e:
            if attempt == retries - 1:
                print("❌ Redis operation failed:", e)
                return None

            await asyncio.sleep(delay * (2 ** attempt))


# =========================
# GRACEFUL SHUTDOWN
# =========================
async def close_redis():
    global _pool

    try:
        if _pool:
            await _pool.disconnect()
            print("✅ Redis pool closed")
    except Exception as e:
        print("⚠️ Redis shutdown error:", e)
