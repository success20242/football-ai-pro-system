import asyncio

from data.football_api import get_live_matches, get_upcoming_matches
from data.odds_api import get_odds
from models.predict import predict
from features.real_features import build_real_features


# =========================
# FEATURE BUILDER (SINGLE SOURCE OF TRUTH)
# =========================
async def build_features(match, odds_map):
    return await build_real_features(match, odds_map)


# =========================
# SAFE FEATURE NORMALIZER
# =========================
def normalize_features(features):
    """
    FORCE STABLE VECTOR FOR MODEL
    """

    if not isinstance(features, list):
        return [0.0, 0.0, 0.0]

    cleaned = []
    for f in features:
        try:
            cleaned.append(float(f))
        except Exception:
            cleaned.append(0.0)

    # enforce EXACT shape for model safety
    return cleaned[:3] + [0.0] * (3 - len(cleaned))


# =========================
# PROCESS MATCH
# =========================
async def process_match(match, odds_map):

    try:
        features = await build_features(match, odds_map)

        features = normalize_features(features)

        prediction = predict(features)

        return {
            "match_id": match.get("id"),
            "league": match.get("league"),
            "home_team": match["homeTeam"]["name"],
            "away_team": match["awayTeam"]["name"],

            # =========================
            # FIXED FEATURE OUTPUT
            # =========================
            "features": {
                "vector": features,
                "form_diff": features[0],
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

    clean = [
        r for r in results
        if isinstance(r, dict) and "prediction" in r
    ]

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
