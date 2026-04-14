import asyncio

from data.football_api import get_live_matches
from data.xg_api import get_team_xg
from data.odds_api import get_odds
from utils.odds_utils import build_odds_map
from models.predict import predict


# =========================
# FEATURE ENGINE (NO PLACEHOLDERS)
# =========================
async def build_features(match, odds_map):

    home_id = match["homeTeam"]["id"]
    away_id = match["awayTeam"]["id"]

    # =========================
    # REAL xG SIGNAL
    # =========================
    home_xg = await get_team_xg(home_id)
    away_xg = await get_team_xg(away_id)

    home_form = float(
        home_xg.get("xg_for", 0.0) - home_xg.get("xg_against", 0.0)
    )
    away_form = float(
        away_xg.get("xg_for", 0.0) - away_xg.get("xg_against", 0.0)
    )

    # =========================
    # ODDS SIGNAL (STRUCTURED)
    # =========================
    match_id = match.get("id")
    odds = odds_map.get(match_id, None)

    if odds:
        home_prob = odds["home_prob"]
        away_prob = odds["away_prob"]

        market_edge = home_prob - away_prob
    else:
        market_edge = 0.0

    return [
        home_form,
        away_form,
        float(market_edge)
    ]


# =========================
# LIVE INFERENCE ENGINE
# =========================
async def run_live_predictions():

    matches_data = await get_live_matches()
    odds_data = await get_odds()

    matches = matches_data.get("matches", [])

    # IMPORTANT: normalize odds once
    odds_map = build_odds_map(odds_data)

    results = []

    for match in matches:

        try:
            features = await build_features(match, odds_map)
            prediction = predict(features)

            results.append({
                "home_team": match["homeTeam"]["name"],
                "away_team": match["awayTeam"]["name"],
                "prediction": prediction,
                "features": {
                    "home_form": features[0],
                    "away_form": features[1],
                    "market_edge": features[2]
                }
            })

        except Exception as e:
            print(f"⚠️ Live engine error: {e}")
            continue

    return results


# =========================
# DEBUG
# =========================
if __name__ == "__main__":
    print(asyncio.run(run_live_predictions()))
