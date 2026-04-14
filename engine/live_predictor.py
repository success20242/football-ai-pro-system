import asyncio

from data.football_api import get_live_matches
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

        home_xg, away_xg = await asyncio.gather(
            get_team_xg(home_id),
            get_team_xg(away_id)
        )

        home_form = home_xg["xg_for"] - home_xg["xg_against"]
        away_form = away_xg["xg_for"] - away_xg["xg_against"]

        momentum = home_form - away_form
        market_edge = momentum * 0.1

        match_id = match.get("id")

        if match_id in odds_map:
            probs = extract_match_probs(odds_map[match_id])
            if probs:
                market_edge = probs["home"] - probs["away"]

        return [home_form, away_form, market_edge]

    except Exception as e:
        raise ValueError(f"Feature build failed: {e}")


# =========================
# LIVE ENGINE
# =========================
async def run_live_predictions():

    matches_data = await get_live_matches()
    odds_data = await get_odds()

    matches = matches_data.get("matches", []) if isinstance(matches_data, dict) else []

    odds_map = {
        o.get("id"): o
        for o in odds_data
        if isinstance(o, dict) and o.get("id") is not None
    }

    tasks = []

    for match in matches:
        tasks.append(process_match(match, odds_map))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # filter errors
    clean_results = [r for r in results if isinstance(r, dict)]

    return clean_results


async def process_match(match, odds_map):
    try:
        features = await build_features(match, odds_map)
        prediction = predict(features)

        return {
            "home_team": match["homeTeam"]["name"],
            "away_team": match["awayTeam"]["name"],
            "prediction": prediction
        }

    except Exception:
        return None
