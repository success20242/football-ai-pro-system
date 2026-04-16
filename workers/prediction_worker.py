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

from core.betting_edge import calculate_ev, get_bet_signal


# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prediction-worker")


# =========================
# SAFE ODDS PARSER
# =========================
def extract_odds_safe(odds: dict):

    if not isinstance(odds, dict):
        return {"home": 2.0, "draw": 3.2, "away": 3.0}

    return {
        "home": float(odds.get("home", 2.0)),
        "draw": float(odds.get("draw", 3.2)),
        "away": float(odds.get("away", 3.0))
    }


# =========================
# PROCESS FUNCTION (FIXED)
# =========================
async def process(payload):

    if not isinstance(payload, dict):
        raise ValueError("Payload must be dict")

    match = payload.get("data")

    if not isinstance(match, dict):
        raise ValueError("Invalid match format")

    match_id = match.get("id")

    # -------------------------
    # RATE LIMITING
    # -------------------------
    await team_stats_limit()
    await odds_api_limit()

    # -------------------------
    # ODDS
    # -------------------------
    odds_list = await get_odds() or []

    odds_map = {
        o.get("id"): o
        for o in odds_list
        if isinstance(o, dict)
    }

    odds = odds_map.get(match_id, {})

    odds = extract_odds_safe(odds)

    # -------------------------
    # FEATURES
    # -------------------------
    features = await build_real_features(match, odds_map)

    if not isinstance(features, list):
        features = [0.0, 0.0, 0.0]

    features = features[:3]

    # -------------------------
    # PREDICTION
    # -------------------------
    prediction = predict(features)

    if not isinstance(prediction, dict):
        raise ValueError("Invalid prediction output")

    label = prediction.get("label", "draw")
    probs = prediction.get("probs", {})

    # -------------------------
    # SELECT PROBABILITY FOR EV
    # -------------------------
    if label == "home":
        prob = probs.get("home", 0.33)
        odds_used = odds["home"]

    elif label == "away":
        prob = probs.get("away", 0.33)
        odds_used = odds["away"]

    else:
        prob = probs.get("draw", 0.34)
        odds_used = odds["draw"]

    # -------------------------
    # BETTING EDGE (CORRECTED)
    # -------------------------
    ev = calculate_ev(prob, odds_used)
    signal = get_bet_signal(ev)

    logger.info(
        f"📊 {label.upper()} | EV={ev:.3f} | SIGNAL={signal} | match={match_id}"
    )

    return {
        "match_id": match_id,
        "features": features,
        "prediction": {
            "label": label,
            "probability": prob,
            "odds_used": odds_used,
            "ev": ev,
            "signal": signal,
            "probs": probs
        }
    }


# =========================
# WORKER LOOP
# =========================
async def worker():

    logger.info("🚀 Prediction worker running...")

    while True:
        try:
            payload = await dequeue_prediction()

            if not payload:
                await asyncio.sleep(0.5)
                continue

            match = payload.get("data")
            match_id = match.get("id") if isinstance(match, dict) else None

            if match_id:
                await mark_processing(match_id)

            try:
                await process(payload)

            except Exception as e:
                logger.warning(f"⚠️ Worker error (retrying): {e}")
                await retry_prediction(payload)

            finally:
                if match_id:
                    await unmark_processing(match_id)

            await asyncio.sleep(0.1)

        except Exception as loop_error:
            logger.error(f"💥 Worker crash recovered: {loop_error}")
            await asyncio.sleep(1)


# =========================
# BOOTSTRAP
# =========================
async def main():
    logger.info("🚀 Starting prediction worker...")
    await worker()


if __name__ == "__main__":
    asyncio.run(main())
