import asyncio
import logging

from data.football_api import get_live_matches, get_upcoming_matches
from core.queue import enqueue_prediction
from core.redis_client import redis_client
from core.rate_limiter import acquire_slot


# =========================
# LOGGING
# =========================
logger = logging.getLogger("live-predictor")
logging.basicConfig(level=logging.INFO)


# =========================
# CONFIG
# =========================
QUEUE_DELAY = 0.02
DEDUP_KEY_PREFIX = "match:queued:"
DEDUP_TTL = 60  # seconds (avoid duplicate enqueue)


# =========================
# DEDUP CHECK (IMPORTANT)
# =========================
async def is_already_queued(match_id: int) -> bool:
    if not match_id:
        return False

    key = f"{DEDUP_KEY_PREFIX}{match_id}"

    exists = await redis_client.get(key)
    if exists:
        return True

    # mark as queued
    await redis_client.set(key, "1", ex=DEDUP_TTL)
    return False


# =========================
# SAFE ENQUEUE
# =========================
async def safe_enqueue(match: dict):

    if not isinstance(match, dict):
        return False

    match_id = match.get("id")

    # 🚫 skip duplicates
    if await is_already_queued(match_id):
        return False

    # 🔒 rate limiter (protect Redis + downstream APIs)
    allowed = await acquire_slot()
    if not allowed:
        await asyncio.sleep(0.2)

    await enqueue_prediction(match)
    await asyncio.sleep(QUEUE_DELAY)

    return True


# =========================
# PRODUCER ENGINE
# =========================
async def run_live_predictions():

    try:
        # -------------------------
        # FETCH LIVE MATCHES
        # -------------------------
        matches_data = await get_live_matches()
        matches = matches_data.get("matches", []) if isinstance(matches_data, dict) else []

        # fallback to upcoming
        if not matches:
            matches_data = await get_upcoming_matches()
            matches = matches_data.get("matches", [])

        if not matches:
            return {"status": "empty", "data": []}

        # -------------------------
        # PROCESS IN PARALLEL (SAFE)
        # -------------------------
        tasks = [safe_enqueue(match) for match in matches]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        queued = sum(1 for r in results if r is True)

        return {
            "status": "queued",
            "total_matches": len(matches),
            "queued": queued,
            "skipped": len(matches) - queued,
            "message": "Matches pushed to prediction queue"
        }

    except Exception as e:
        logger.error(f"Live predictor error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


# =========================
# DEBUG
# =========================
if __name__ == "__main__":
    print(asyncio.run(run_live_predictions()))
