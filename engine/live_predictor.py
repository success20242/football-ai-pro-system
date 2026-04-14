import asyncio

from data.football_api import get_live_matches, get_upcoming_matches
from data.odds_api import get_odds
from utils.odds_utils import extract_match_probs
from models.predict import predict
from features.real_features import build_real_features


# =========================
# FEATURE BUILDER (CLEAN)
# =========================
async def build_features(match, odds_map):

    # 👉 FULLY DELEGATE TO FEATURE ENGINE
    return await build_real_features(match, odds_map)


# =========================
# PROCESS MATCH
# =========================
async def process_match(match, odds_map):

    try:
        features = await build_features(match, odds_map)
        prediction = predict(features)

        return {
            "match_id": match.get("id"),
            "league": match.get("league"),
            "home_team": match["homeTeam"]["name"],
            "away_team": match["awayTeam"]["name"],
            "features": {
                "vector": features,
                "strength_diff": features[0],
                "xg_diff": features[1],
                "market_bias": features[2]
            },
            "prediction": prediction
        }

    except Exception as e:
        return {
            "error": str(e),
            "match": match.get("id")
        }


# =========================
# LIVE ENGINE
# =========================
async def run_live_predictions():

    matches_data = await get_live_matches()
    matches = matches_data.get("matches", []) if isinstance(matches_data, dict) else []

    if not matches:
        matches_data = await get_upcoming_matches()
        matches = matches_data.get("matches", [])

    if not matches:
        return {"status": "empty", "data": []}

    odds_raw = await get_odds()

    odds_map = {
        o.get("id"): o
        for o in odds_raw
        if isinstance(o, dict) and o.get("id") is not None
    }

    tasks = [process_match(match, odds_map) for match in matches]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    clean = [r for r in results if isinstance(r, dict) and "prediction" in r]

    return {
        "status": "success",
        "total": len(clean),
        "data": clean
    }


# =========================
# DEBUG
# =========================
if __name__ == "__main__":
    print(asyncio.run(run_live_predictions()))
