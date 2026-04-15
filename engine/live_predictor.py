import asyncio
import logging

from data.football_api import get_live_matches, get_upcoming_matches
from data.odds_api import get_odds
from features.real_features import build_real_features
from models.predict import predict

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
DEDUP_TTL = 60


# =========================
# FORMAT OUTPUT
# =========================
def format_prediction(pred):
    try:
        return {
            "prediction": pred.get("label"),
            "confidence": round(float(pred.get("confidence", 0.5)), 4),
            "probabilities": pred.get("probs", {})
        }
    except:
        return {
            "prediction": "UNKNOWN",
            "confidence": 0.0,
            "probabilities": {}
        }


# =========================
# DEDUP CHECK
# =========================
async def is_already_queued(match_id: int) -> bool:
    if not match_id:
        return False

    key = f"{DEDUP_KEY_PREFIX}{match_id}"

    exists = await redis_client.get(key)
    if exists:
        return True

    await redis_client.set(key, "1", ex=DEDUP_TTL)
    return False


# =========================
# SAFE ENQUEUE
# =========================
async def safe_enqueue(match: dict):

    if not isinstance(match, dict):
        return False

    match_id = match.get("id")

    if await is_already_queued(match_id):
        return False

    allowed = await acquire_slot()
    if not allowed:
        await asyncio.sleep(0.2)

    await enqueue_prediction(match)
    await asyncio.sleep(QUEUE_DELAY)

    return True


# =========================
# 🔥 MAIN ENGINE (HYBRID)
# =========================
async def run_live_predictions():

    try:
        # -------------------------
        # 1. GET MATCHES
        # -------------------------
        matches_data = await get_live_matches()
        matches = matches_data.get("matches", []) if isinstance(matches_data, dict) else []

        # fallback → upcoming
        if not matches:
            matches_data = await get_upcoming_matches()
            matches = matches_data.get("matches", []) if isinstance(matches_data, dict) else []

        if not matches:
            return {
                "status": "empty",
                "data": [],
                "message": "No matches available"
            }

        # -------------------------
        # 2. GET ODDS
        # -------------------------
        odds_list = await get_odds()
        odds_map = {o["match_key"]: o for o in odds_list}

        results = []

        # -------------------------
        # 3. PROCESS MATCHES
        # -------------------------
        for match in matches:

            # 🔥 BUILD FEATURES
            features = await build_real_features(match, odds_map)

            # 🔥 PREDICT
            pred = predict(features)

            # 🔥 FORMAT
            formatted = format_prediction(pred)

            # 🔥 QUEUE IN BACKGROUND
            asyncio.create_task(safe_enqueue(match))

            results.append({
                "match": match,
                "prediction": formatted
            })

        return {
            "status": "success",
            "total": len(results),
            "data": results
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
