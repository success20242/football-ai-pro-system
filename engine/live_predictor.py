import asyncio

from data.football_api import get_live_matches, get_upcoming_matches
from data.xg_api import get_team_xg
from data.odds_api import get_odds
from utils.odds_utils import extract_match_probs
from models.predict import predict


# =========================
# FEATURE BUILDER
# =========================
async def build_features(match, odds_map):
    try:
        home_id = match["homeTeam"]["id"]
        away_id = match["awayTeam"]["id"]

        # 🔥 parallel xG fetch
        home_xg, away_xg = await asyncio.gather(
            get_team_xg(home_id),
            get_team_xg(away_id)
        )

        # safe defaults
        home_form = (home_xg.get("xg_for", 0) - home_xg.get("xg_against", 0)) if home_xg else 0
        away_form = (away_xg.get("xg_for", 0) - away_xg.get("xg_against", 0)) if away_xg else 0

        momentum = home_form - away_form
        market_edge = momentum * 0.1

        # 🔥 odds integration
        match_id = match.get("id")

        if match_id and match_id in odds_map:
            probs = extract_match_probs(odds_map[match_id])
            if probs:
                market_edge = probs.get("home", 0) - probs.get("away", 0)

        return [home_form, away_form, market_edge]

    except Exception as e:
        raise ValueError(f"Feature build failed: {e}")


# =========================
# PROCESS SINGLE MATCH
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
            "prediction": prediction
        }

    except Exception:
        return None


# =========================
# LIVE ENGINE
# =========================
async def run_live_predictions():

    # -------------------------
    # 1. GET MATCHES
    # -------------------------
    matches_data = await get_live_matches()

    matches = matches_data.get("matches", []) if isinstance(matches_data, dict) else []

    # 🔥 fallback if no live matches
    if not matches:
        matches_data = await get_upcoming_matches()
        matches = matches_data.get("matches", [])

    if not matches:
        return []

    # -------------------------
    # 2. GET ODDS
    # -------------------------
    odds_data = await get_odds()

    odds_map = {
        o.get("id"): o
        for o in odds_data
        if isinstance(o, dict) and o.get("id") is not None
    }

    # -------------------------
    # 3. PARALLEL PROCESSING
    # -------------------------
    tasks = [process_match(match, odds_map) for match in matches]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # -------------------------
    # 4. CLEAN RESULTS
    # -------------------------
    clean_results = [
        r for r in results
        if isinstance(r, dict)
    ]

    return clean_results


# =========================
# LOCAL TEST
# =========================
if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run_live_predictions()))
