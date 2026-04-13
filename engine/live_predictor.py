import asyncio

from data.football_api import get_live_matches, get_team_stats
from data.odds_api import get_odds
from models.predict import predict


# =========================
# REAL FEATURE ENGINE
# =========================
async def build_real_features(match):

    home_team = match["homeTeam"]["name"]
    away_team = match["awayTeam"]["name"]

    # -------------------------
    # 1. TEAM STATS (REAL API)
    # -------------------------
    home_stats = await get_team_stats(match["homeTeam"]["id"])
    away_stats = await get_team_stats(match["awayTeam"]["id"])

    try:
        home_attack = home_stats["counters"]["goals"]
        away_attack = away_stats["counters"]["goals"]

        home_against = home_stats["counters"]["conceded"]
        away_against = away_stats["counters"]["conceded"]

    except Exception:
        return None  # no fake fallback

    home_form = (home_attack - home_against)
    away_form = (away_attack - away_against)

    momentum = home_form - away_form

    # -------------------------
    # 2. MARKET EDGE (REAL ODDS LATER MATCHED)
    # -------------------------
    market_edge = momentum * 0.1

    return [home_form, away_form, market_edge]


# =========================
# LIVE ENGINE
# =========================
async def run_live_predictions():

    matches_data = await get_live_matches()
    odds_data = await get_odds()

    matches = matches_data.get("matches", [])

    results = []

    for match in matches:

        features = await build_real_features(match)

        if features is None:
            continue

        prediction = predict(features)

        results.append({
            "home_team": match["homeTeam"]["name"],
            "away_team": match["awayTeam"]["name"],
            "prediction": prediction
        })

    return results


# DEBUG
if __name__ == "__main__":
    print(asyncio.run(run_live_predictions()))
