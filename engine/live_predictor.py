import asyncio

from data.football_api import get_live_matches, get_upcoming_matches
from data.xg_api import get_team_xg
from data.odds_api import get_odds
from utils.odds_utils import extract_match_probs
from models.predict import predict


# =========================
# FEATURE BUILDER (UPGRADED)
# =========================
async def build_features(match, odds_map):

    try:
        home_id = match["homeTeam"]["id"]
        away_id = match["awayTeam"]["id"]

        # -------------------------
        # xG DATA (SAFE + DIVERSE)
        # -------------------------
        home_xg, away_xg = await asyncio.gather(
            get_team_xg(home_id),
            get_team_xg(away_id)
        )

        def safe_xg(xg):
            if not xg:
                return {"xg_for": 1.0, "xg_against": 1.0}
            return xg

        home_xg = safe_xg(home_xg)
        away_xg = safe_xg(away_xg)

        home_form = home_xg["xg_for"] - home_xg["xg_against"]
        away_form = away_xg["xg_for"] - away_xg["xg_against"]

        # -------------------------
        # DIFFERENTIAL FEATURES (IMPORTANT)
        # -------------------------
        form_diff = home_form - away_form
        total_form = home_form + away_form

        momentum = form_diff * 0.6 + total_form * 0.2

        # -------------------------
        # ODDS SIGNAL (SOFT, NOT OVERRIDE)
        # -------------------------
        market_edge = 0.0

        match_id = match.get("id")

        if match_id and match_id in odds_map:
            probs = extract_match_probs(odds_map[match_id])
            if probs:
                market_edge = (
                    (probs.get("home", 0) - probs.get("away", 0)) * 0.3
                )

        # -------------------------
        # FINAL FEATURE VECTOR (RICHER)
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
            "features": features,   # 🔥 DEBUG (VERY IMPORTANT)
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

    # fallback
    if not matches:
        matches_data = await get_upcoming_matches()
        matches = matches_data.get("matches", [])

    if not matches:
        return {
            "status": "empty",
            "data": []
        }

    odds_data = await get_odds()

    odds_map = {
        o.get("id"): o
        for o in odds_data
        if isinstance(o, dict) and o.get("id") is not None
    }

    tasks = [process_match(match, odds_map) for match in matches]

    results = await asyncio.gather(*tasks)

    clean = [r for r in results if r and "prediction" in r]

    return {
        "status": "success",
        "total": len(clean),
        "data": clean
    }


# =========================
# TEST
# =========================
if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run_live_predictions()))
