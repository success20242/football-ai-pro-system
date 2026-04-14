import asyncio

from data.football_api import get_live_matches
from data.xg_api import get_team_xg
from data.odds_api import get_odds
from features.odds_features import extract_match_probs
from models.predict import predict


# =========================
# FEATURE BUILDER (INSTITUTIONAL VERSION)
# =========================
async def build_features(match, odds_list):

    home_id = match["homeTeam"]["id"]
    away_id = match["awayTeam"]["id"]

    # =========================
    # xG SIGNAL (REAL DATA)
    # =========================
    home_xg = await get_team_xg(home_id)
    away_xg = await get_team_xg(away_id)

    home_form = float(home_xg.get("xg_for", 1.0) - home_xg.get("xg_against", 1.0))
    away_form = float(away_xg.get("xg_for", 1.0) - away_xg.get("xg_against", 1.0))

    momentum = home_form - away_form

    # =========================
    # MARKET SIGNAL (SAFE MATCHING)
    # =========================
    market_edge = momentum * 0.1  # fallback default

    for odds in odds_list:

        # try to match by team names (more reliable than ID)
        if "home_team" in odds and "away_team" in odds:

            if (odds["home_team"] == match["homeTeam"]["name"] and
                odds["away_team"] == match["awayTeam"]["name"]):

                market_probs = extract_match_probs(odds)

                if market_probs:
                    market_edge = market_probs["home"] - market_probs["away"]

                break

    return [
        home_form,
        away_form,
        market_edge
    ]


# =========================
# LIVE ENGINE
# =========================
async def run_live_predictions():

    matches_data = await get_live_matches()
    odds_data = await get_odds()

    matches = matches_data.get("matches", [])

    results = []

    for match in matches:

        try:
            features = await build_features(match, odds_data)
            prediction = predict(features)

            results.append({
                "home_team": match["homeTeam"]["name"],
                "away_team": match["awayTeam"]["name"],
                "prediction": prediction
            })

        except Exception as e:
            print(f"⚠️ Error: {e}")
            continue

    return results


# DEBUG
if __name__ == "__main__":
    print(asyncio.run(run_live_predictions()))
