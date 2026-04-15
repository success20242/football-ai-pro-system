import json
import asyncio
from typing import Optional, Dict, Any
from core.redis_client import redis_client

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
        return json.loads(data)
    except Exception:
        return None


def safe_json_dump(data):
    try:
        return json.dumps(data)
    except Exception:
        return "{}"


# =========================
# ENQUEUE
# =========================
async def enqueue_prediction(match: Dict[str, Any]):
    """
    Add match to queue
    """
    payload = {
        "data": match,
        "retries": 0
    }

    await redis_client.rpush(QUEUE_KEY, safe_json_dump(payload))


# =========================
# DEQUEUE
# =========================
async def dequeue_prediction() -> Optional[Dict[str, Any]]:
    """
    Pop from queue safely
    """
    raw = await redis_client.lpop(QUEUE_KEY)

    if not raw:
        return None

    payload = safe_json_load(raw)
    if not payload:
        return None

    return payload


# =========================
# MARK PROCESSING (LOCK)
# =========================
async def mark_processing(match_id):
    await redis_client.sadd(PROCESSING_KEY, match_id)


async def unmark_processing(match_id):
    await redis_client.srem(PROCESSING_KEY, match_id)


# =========================
# RETRY LOGIC
# =========================
async def retry_prediction(payload: Dict[str, Any]):
    """
    Push failed jobs into retry queue with delay
    """
    retries = payload.get("retries", 0)

    if retries >= MAX_RETRIES:
        return  # drop permanently

    payload["retries"] = retries + 1

    # delay before retry
    await asyncio.sleep(RETRY_DELAY)

    await redis_client.rpush(RETRY_KEY, safe_json_dump(payload))


async def requeue_failed():
    """
    Move retry queue back into main queue
    """
    while True:
        raw = await redis_client.lpop(RETRY_KEY)

        if not raw:
            break

        await redis_client.rpush(QUEUE_KEY, raw)


# =========================
# RATE LIMIT CONTROL
# =========================
async def throttle(rate_limit: int = 5):
    """
    Simple rate limiter:
    allows X requests per second
    """
    await asyncio.sleep(1 / rate_limit)


# =========================
# WORKER LOOP (IMPORTANT)
# =========================
async def worker(process_func):
    """
    process_func = async function(match_dict)
    """

    while True:
        payload = await dequeue_prediction()

        if not payload:
            await asyncio.sleep(1)
            continue

        match = payload.get("data")
        match_id = match.get("id") if isinstance(match, dict) else None

        try:
            if match_id:
                await mark_processing(match_id)

            # 🔥 throttle API calls
            await throttle(5)

            await process_func(match)

        except Exception:
            await retry_prediction(payload)

        finally:
            if match_id:
                await unmark_processing(match_id)
