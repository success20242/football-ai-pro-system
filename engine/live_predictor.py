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
# SAFE FEATURE NORMALIZER (FIXED CONTRACT = 4 FEATURES)
# =========================
def normalize_features(features):
    """
    MODEL CONTRACT:
    MUST ALWAYS RETURN 4 FEATURES:
    [strength_diff, market_strength, xg_diff, entropy]
    """

    if not isinstance(features, list):
        return [0.0, 0.0, 0.0, 0.0]

    cleaned = []
    for f in features:
        try:
            cleaned.append(float(f))
        except Exception:
            cleaned.append(0.0)

    # enforce EXACT 4-DIM VECTOR
    cleaned = cleaned[:4]

    while len(cleaned) < 4:
        cleaned.append(0.0)

    return cleaned


# =========================
# PROCESS MATCH
# =========================
async def process_match(match, odds_map):

    try:
        # FIX: guard against malformed match
        if not isinstance(match, dict):
            return None

        features = await build_features(match, odds_map)
        features = normalize_features(features)

        prediction = predict(features)

        home_team = match.get("homeTeam")
        away_team = match.get("awayTeam")

        return {
            "match_id": match.get("id"),
            "league": match.get("league"),

            "home_team": home_team.get("name") if isinstance(home_team, dict) else None,
            "away_team": away_team.get("name") if isinstance(away_team, dict) else None,

            "features": {
                "vector": features,
                "form_diff": features[0],
                "xg_diff": features[1],
                "market_bias": features[2],
                "entropy": features[3]
            },

            "prediction": prediction
        }

    except Exception as e:
        return {
            "error": str(e),
            "match": match.get("id") if isinstance(match, dict) else None
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

    # 🔥 FIX: odds API uses match_id, not id
    odds_map = {
        o.get("match_id"): o
        for o in odds_raw
        if isinstance(o, dict) and o.get("match_id") is not None
    }

    tasks = [process_match(match, odds_map) for match in matches]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    clean = [
        r for r in results
        if isinstance(r, dict)
        and r.get("prediction") is not None
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
