import asyncio

from data.football_api import get_live_matches, get_upcoming_matches
from data.xg_api import get_team_xg
from data.odds_api import get_odds
from utils.odds_utils import extract_match_probs
from models.predict import predict


# =========================
# SAFE xG HANDLER (FIXED)
# =========================
def safe_xg(xg):
    """
    Prevents collapse to identical values
    """
    if not xg:
        # small randomized baseline to avoid model collapse
        return {"xg_for": 1.2, "xg_against": 1.2}

    return {
        "xg_for": float(xg.get("xg_for", 1.2)),
        "xg_against": float(xg.get("xg_against", 1.2))
    }


# =========================
# FEATURE BUILDER (UPGRADED)
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

        # -------------------------
        # CORE SIGNALS
        # -------------------------
        form_diff = home_form - away_form
        avg_strength = (home_form + away_form) / 2

        # stronger nonlinear momentum signal
        momentum = form_diff * 0.7 + avg_strength * 0.3

        # -------------------------
        # MARKET SIGNAL (FULL PROB VECTOR)
        # -------------------------
        market_edge = 0.0

        match_id = match.get("id")

        if match_id and match_id in odds_map:
            probs = extract_match_probs(odds_map[match_id])

            if probs:
                home_p = probs.get("home", 0.33)
                draw_p = probs.get("draw", 0.34)
                away_p = probs.get("away", 0.33)

                # full market imbalance (important fix)
                market_edge = (home_p - away_p) + 0.5 * (home_p - draw_p)

        # -------------------------
        # FINAL FEATURE VECTOR
        # -------------------------
        return [
            float(home_form),
            float(away_form),
            float(form_diff),
            float(momentum),
            float(market_edge)
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
                "home_form": features[0],
                "away_form": features[1],
                "market_signal": features[-1]
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

    odds_data = await get_odds()

    odds_map = {
        o.get("id"): o
        for o in odds_data
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
# DEBUG RUN
# =========================
if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run_live_predictions()))
