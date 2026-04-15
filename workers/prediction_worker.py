import asyncio
import logging

from core.queue import (
    dequeue_prediction,
    retry_prediction,
    mark_processing,
    unmark_processing
)
from core.rate_limiter import team_stats_limit, odds_api_limit
from data.odds_api import get_odds
from features.real_features import build_real_features
from models.predict import predict


# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prediction-worker")


# =========================
# PROCESS FUNCTION
# =========================
async def process(payload):
    """
    payload = {
        "data": match,
        "retries": int
    }
    """

    match = payload.get("data")

    if not isinstance(match, dict):
        raise ValueError("Invalid match format")

    match_id = match.get("id")

    # -------------------------
    # RATE LIMIT (CRITICAL)
    # -------------------------
    await team_stats_limit()
    await odds_api_limit()

    # -------------------------
    # FETCH ODDS (OPTIONAL)
    # -------------------------
    odds_list = await get_odds()

    odds_map = {
        o.get("match_id"): o
        for o in odds_list
        if isinstance(o, dict)
    }

    # -------------------------
    # BUILD FEATURES
    # -------------------------
    features = await build_real_features(match, odds_map)

    # 🔥 IMPORTANT: enforce model shape (3 or 4 depending on your model)
    features = features[:3] if isinstance(features, list) else [0.0, 0.0, 0.0]

    # -------------------------
    # PREDICT
    # -------------------------
    prediction = predict(features)

    logger.info(f"✅ Prediction done: {match_id}")

    return {
        "match_id": match_id,
        "features": features,
        "prediction": prediction
    }


# =========================
# WORKER LOOP
# =========================
async def worker():
    logger.info("🚀 Prediction worker running...")

    while True:
        payload = await dequeue_prediction()

        if not payload:
            await asyncio.sleep(0.5)
            continue

        match = payload.get("data")
        match_id = match.get("id") if isinstance(match, dict) else None

        try:
            if match_id:
                await mark_processing(match_id)

            await process(payload)

        except Exception as e:
            logger.warning(f"⚠️ Worker error (retrying): {e}")
            await retry_prediction(payload)

        finally:
            if match_id:
                await unmark_processing(match_id)

            # small delay to avoid burst
            await asyncio.sleep(0.1)
