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
        matches = []

        # =========================
        # 1. TRY LIVE MATCHES (API-FOOTBALL FIRST)
        # =========================
        try:
            matches_data = await get_live_matches()

            # handle API-Football 403 or bad response safely
            if isinstance(matches_data, dict):
                matches = matches_data.get("matches", []) or []
        except Exception as e:
            logger.warning(f"API-Football live fetch failed: {e}")
            matches = []

        # =========================
        # 2. FALLBACK (football-data.org)
        # =========================
        if not matches:
            try:
                matches_data = await get_upcoming_matches()
                if isinstance(matches_data, dict):
                    matches = matches_data.get("matches", []) or []
            except Exception as e:
                logger.error(f"Fallback fetch failed: {e}")
                matches = []

        # =========================
        # 3. HARD SAFETY CHECK
        # =========================
        if not matches:
            return {
                "status": "empty",
                "data": [],
                "message": "No live matches available from any provider"
            }

        # =========================
        # 4. PROCESS MATCHES
        # =========================
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
