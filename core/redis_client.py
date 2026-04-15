import os
import redis.asyncio as redis
from dotenv import load_dotenv

# =========================
# LOAD ENV
# =========================
load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))


# =========================
# SINGLETON CLIENT (IMPORTANT)
# =========================
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True,
    health_check_interval=30,
)


# =========================
# OPTIONAL HEALTH CHECK
# =========================
async def check_redis():
    try:
        return await redis_client.ping()
    except Exception as e:
        print("Redis connection failed:", e)
        return False
