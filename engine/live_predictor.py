import asyncio
import logging

from data.football_api import get_live_matches, get_upcoming_matches
from data.odds_api import get_odds
from features.real_features import build_real_features, normalize_team
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
# SAFE PREDICTION FORMATTER (FIXED)
# =========================
def format_prediction(pred: dict):

    if not isinstance(pred, dict):
        return {
            "prediction": "unknown",
            "confidence": 0.0,
            "probabilities": {}
        }

    probs = pred.get("probs", {})

    if not probs:
        return {
            "prediction": pred.get("label", "unknown"),
            "confidence": pred.get("confidence", 0.5),
            "probabilities": {}
        }

    label = max(probs, key=probs.get)
    confidence = float(probs[label])

    return {
        "prediction": label,
        "confidence": confidence,
        "probabilities": probs
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
# SAFE ENQUEUE (FIXED)
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
# MAIN ENGINE (FIXED)
# =========================
async def run_live_predictions():

    try:
        # -------------------------
        # MATCHES
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
        # ODDS MAP
        # -------------------------
        odds_list = await get_odds() or []

        odds_map = {
            o.get("match_key"): o
            for o in odds_list
            if isinstance(o, dict)
        }

        results = []

        # -------------------------
        # PROCESS MATCHES
        # -------------------------
        for match in matches:

            try:
                # FEATURES
                features = await build_real_features(match, odds_map)

                if not isinstance(features, list):
                    features = [0.0, 0.0, 0.0]

                features = features[:3]

                # PREDICTION
                pred = predict(features)
                formatted = format_prediction(pred)

                probs = formatted.get("probabilities", {})

                home_p = probs.get("home", 0.33)
                draw_p = probs.get("draw", 0.34)
                away_p = probs.get("away", 0.33)

                # MATCH KEY
                home_name = normalize_team(match.get("homeTeam", {}).get("name"))
                away_name = normalize_team(match.get("awayTeam", {}).get("name"))

                match_key = f"{home_name}_{away_name}"

                odds = odds_map.get(match_key, {}) or {}

                home_odds = float(odds.get("home", 2.0))
                draw_odds = float(odds.get("draw", 3.2))
                away_odds = float(odds.get("away", 2.0))

                # EV CALCULATION (ALL OUTCOMES)
                ev_home = calculate_ev(home_p, home_odds)
                ev_draw = calculate_ev(draw_p, draw_odds)
                ev_away = calculate_ev(away_p, away_odds)

                best = max(
                    [("HOME", ev_home), ("DRAW", ev_draw), ("AWAY", ev_away)],
                    key=lambda x: x[1]
                )

                signal = get_bet_signal(best[1])

                # enqueue async safely
                asyncio.create_task(safe_enqueue(match))

                results.append({
                    "match": match,
                    "prediction": {
                        **formatted,
                        "ev": {
                            "home": round(ev_home, 4),
                            "draw": round(ev_draw, 4),
                            "away": round(ev_away, 4),
                        },
                        "best_bet": best[0],
                        "signal": signal
                    }
                })

            except Exception as e:
                logger.warning(f"⚠️ Match skipped: {e}")

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
