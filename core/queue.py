import json
import asyncio
import logging
from typing import Optional, Dict, Any
from core.redis_client import redis_client

logger = logging.getLogger("queue")

QUEUE_KEY = "football:prediction_queue"
RETRY_KEY = "football:prediction_retry"
PROCESSING_KEY = "football:processing"

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


# =========================
# SAFE JSON
# =========================
def safe_json_load(data):
    try:
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        return json.loads(data)
    except Exception as e:
        logger.warning(f"JSON LOAD ERROR: {e}")
        return None


def safe_json_dump(data):
    try:
        return json.dumps(data)
    except Exception as e:
        logger.warning(f"JSON DUMP ERROR: {e}")
        return "{}"


# =========================
# ENQUEUE
# =========================
async def enqueue_prediction(match: Dict[str, Any]):
    payload = {"data": match, "retries": 0}
    await redis_client.rpush(QUEUE_KEY, safe_json_dump(payload))


# =========================
# DEQUEUE (MAIN + RETRY SAFE)
# =========================
async def dequeue_prediction() -> Optional[Dict[str, Any]]:

    # 1st try main queue
    raw = await redis_client.lpop(QUEUE_KEY)

    # fallback retry queue
    if not raw:
        raw = await redis_client.lpop(RETRY_KEY)

    if not raw:
        return None

    return safe_json_load(raw)


# =========================
# PROCESSING LOCK
# =========================
async def mark_processing(match_id):
    if match_id:
        await redis_client.sadd(PROCESSING_KEY, match_id)


async def unmark_processing(match_id):
    if match_id:
        await redis_client.srem(PROCESSING_KEY, match_id)


# =========================
# RETRY SYSTEM (FIXED)
# =========================
async def retry_prediction(payload: Dict[str, Any]):

    if not isinstance(payload, dict):
        return

    retries = payload.get("retries", 0)

    if retries >= MAX_RETRIES:
        logger.warning("❌ DROPPED JOB (max retries reached)")
        return

    payload["retries"] = retries + 1

    # small backoff (non-blocking system-wide impact)
    await asyncio.sleep(RETRY_DELAY)

    await redis_client.rpush(RETRY_KEY, safe_json_dump(payload))


# =========================
# BACKLOG RECOVERY LOOP
# =========================
async def requeue_failed():

    while True:
        raw = await redis_client.lpop(RETRY_KEY)

        if not raw:
            await asyncio.sleep(5)
            continue

        await redis_client.rpush(QUEUE_KEY, raw)


# =========================
# RATE LIMIT
# =========================
async def throttle(rate_limit: int = 5):
    await asyncio.sleep(1 / rate_limit)


# =========================
# WORKER LOOP (HARDENED)
# =========================
async def worker(process_func):

    logger.info("🚀 Worker started")

    while True:

        payload = await dequeue_prediction()

        if not payload:
            await asyncio.sleep(1)
            continue

        try:
            match = payload.get("data") if isinstance(payload, dict) else None

            if not isinstance(match, dict):
                continue

            match_id = match.get("id")

            await mark_processing(match_id)
            await throttle(5)

            await process_func(match)

        except Exception as e:
            logger.error(f"⚠️ Worker error: {e}")
            await retry_prediction(payload)

        finally:
            try:
                if isinstance(payload, dict):
                    match = payload.get("data", {})
                    await unmark_processing(match.get("id"))
            except:
                pass
