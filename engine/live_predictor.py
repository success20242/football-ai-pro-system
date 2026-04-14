import asyncio

from data.football_api import get_live_matches, get_upcoming_matches
from data.xg_api import get_team_xg
from data.odds_api import get_odds
from utils.odds_utils import extract_match_probs
from models.predict import predict


# =========================
# SAFE xG HANDLER (IMPROVED)
# =========================
def safe_xg(xg):
    if not xg:
        # small realistic baseline (NOT constant collapse)
        return {
            "xg_for": 1.3,
            "xg_against": 1.3
        }

    return {
        "xg_for": float(xg.get("xg_for", 1.3)),
        "xg_against": float(xg.get("xg_against", 1.3))
    }


# =========================
# FEATURE BUILDER
# =========================
async def build_features(match, odds_map):

    try:
        home_id = match["homeTeam"]["id"]
        away_id = match["awayTeam"]["id"]

        # -------------------------
        # xG FETCH
        # -------------------------
        home_xg, away_xg = await asyncio.gather(
            get_team_xg(home_id),
            get_team_xg(away_id)
        )

        home_xg = safe_xg(home_xg)
        away_xg = safe_xg(away_xg)

        home_form = home_xg["xg_for"] - home_xg["xg_against"]
        away_form = away_xg["xg_for"] - away_xg["xg_against"]

        form_diff = home_form - away_form
        avg_form = (home_form + away_form) / 2

        momentum = form_diff * 0.6 + avg_form * 0.2

        # -------------------------
        # MARKET SIGNAL (FIXED)
        # -------------------------
        market_edge = 0.0

        match_id = match.get("id")

        odds_data = odds_map.get(match_id)

        if odds_data:
            probs = extract_match_probs(odds_data)

            if probs:
                # TRUE MARKET IMBALANCE (normalized)
                market_edge = (
                    probs["home"] - probs["away"]
                )

        # -------------------------
        # FINAL FEATURE VECTOR
        # -------------------------
        return [
            home_form,
            away_form,
            form_diff,
            momentum,
            market_edge
        ]

    except Exception as e:
        raise ValueError(f"Feature build failed: {e}")


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
                "form_diff": features[2],
                "market_edge": features[4]
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

    # IMPORTANT FIX: use build_odds_map if available OR fallback-safe mapping
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
    import asyncio
    print(asyncio.run(run_live_predictions()))
