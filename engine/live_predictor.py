import asyncio
import logging

from data.football_api import get_live_matches, get_upcoming_matches
from data.odds_api import get_odds
from features.real_features import build_real_features
from models.predict import predict

from core.queue import enqueue_prediction
from core.redis_client import redis_client
from core.rate_limiter import acquire_slot
from core.betting_edge import calculate_ev, get_bet_signal

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
# FORMAT PREDICTION (FIXED)
# =========================
def format_prediction(pred: dict):

    if not isinstance(pred, dict):
        return {
            "prediction": "UNKNOWN",
            "confidence": 0.0,
            "probabilities": {}
        }

    prob = (
        pred.get("probability")
        or pred.get("confidence")
        or 0.5
    )

    label = (
        pred.get("label")
        or ("HOME" if prob >= 0.5 else "AWAY")
    )

    return {
        "prediction": label,
        "confidence": float(prob),
        "probabilities": pred.get("probs", {})
    }


# =========================
# DEDUP
# =========================
async def is_already_queued(match_id: int) -> bool:

    if not match_id:
        return False

    key = f"{DEDUP_KEY_PREFIX}{match_id}"

    if await redis_client.get(key):
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

    if not await acquire_slot():
        await asyncio.sleep(0.2)

    await enqueue_prediction(match)
    await asyncio.sleep(QUEUE_DELAY)

    return True


# =========================
# MAIN ENGINE (FIXED + BETTING EDGE)
# =========================
async def run_live_predictions():

    try:
        # -------------------------
        # 1. MATCHES
        # -------------------------
        matches_data = await get_live_matches()
        matches = matches_data.get("matches", []) if isinstance(matches_data, dict) else []

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
        # 2. ODDS (FIXED MAPPING)
        # -------------------------
        odds_list = await get_odds() or []

        odds_map = {}
        for o in odds_list:
            if not isinstance(o, dict):
                continue

            key = (
                o.get("match_id")
                or o.get("match_key")
                or o.get("id")
            )

            if key:
                odds_map[key] = o

        results = []

        # -------------------------
        # 3. PROCESS MATCHES
        # -------------------------
        for match in matches:

            match_id = match.get("id")

            # FEATURES
            features = await build_real_features(match, odds_map)

            if not isinstance(features, list):
                features = [0.0, 0.0, 0.0]

            features = features[:3]

            # PREDICT
            pred = predict(features)
            formatted = format_prediction(pred)

            # ODDS
            odds = odds_map.get(match_id, {}) or {}
            home_odds = odds.get("home_odds", 2.0)

            # BETTING EDGE
            prob = formatted.get("confidence", 0.5)
            ev = calculate_ev(prob, home_odds)
            signal = get_bet_signal(ev)

            # QUEUE IN BACKGROUND
            asyncio.create_task(safe_enqueue(match))

            results.append({
                "match": match,
                "prediction": {
                    **formatted,
                    "ev": ev,
                    "signal": signal
                }
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
