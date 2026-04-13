import asyncio

from data.football_api import get_live_matches
from data.xg_api import get_team_xg
from data.odds_api import get_odds
from features.odds_features import extract_match_probs
from models.predict import predict


# =========================
# FEATURE BUILDER (REAL QUANT)
# =========================
async def build_features(match, odds_map):

    home_id = match["homeTeam"]["id"]
    away_id = match["awayTeam"]["id"]

    # -------------------------
    # xG FEATURES (REAL SIGNAL)
    # -------------------------
    home_xg = await get_team_xg(home_id)
    away_xg = await get_team_xg(away_id)

    home_form = home_xg["xg_for"] - home_xg["xg_against"]
    away_form = away_xg["xg_for"] - away_xg["xg_against"]

    # -------------------------
    # MOMENTUM (RELATIVE EDGE)
    # -------------------------
    momentum = home_form - away_form

    # -------------------------
    # MARKET EDGE (ODDS SIGNAL)
    # -------------------------
    match_odds = odds_map.get(match["id"], None)

    if match_odds:
        market_probs = extract_match_probs(match_odds)
        market_edge = market_probs["home"] - market_probs["away"]
    else:
        market_edge = momentum * 0.1

    return [home_form, away_form, market_edge]


# =========================
# LIVE ENGINE
# =========================
async def run_live_predictions():

    matches_data = await get_live_matches()
    odds_data = await get_odds()

    matches = matches_data.get("matches", [])

    # map odds by match id (CRITICAL FIX)
    odds_map = {
        o["id"]: o for o in odds_data
    }

    results = []

    for match in matches:

        try:
            features = await build_features(match, odds_map)
            prediction = predict(features)

            results.append({
                "home_team": match["homeTeam"]["name"],
                "away_team": match["awayTeam"]["name"],
                "prediction": prediction
            })

        except Exception:
            continue

    return results

# DEBUG
if __name__ == "__main__":
    print(asyncio.run(run_live_predictions()))
