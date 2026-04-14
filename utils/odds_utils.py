import asyncio
import pandas as pd

from data.football_api import get_fixtures
from data.xg_api import get_team_xg
from data.odds_api import get_odds
from utils.odds_utils import build_odds_map


# =========================
# BUILD REAL TRAINING DATASET
# =========================
async def build_dataset(competition="PL", limit=200):
    """
    Builds ML-ready dataset from real football data.
    """

    fixtures_data = await get_fixtures(competition)
    odds_data = await get_odds()

    matches = fixtures_data.get("matches", [])

    # limit dataset size for safety
    matches = matches[:limit]

    odds_map = build_odds_map(odds_data)

    dataset = []

    for match in matches:

        try:
            if match.get("status") != "FINISHED":
                continue

            home_id = match["homeTeam"]["id"]
            away_id = match["awayTeam"]["id"]

            home_xg = await get_team_xg(home_id)
            away_xg = await get_team_xg(away_id)

            home_form = home_xg["xg_for"] - home_xg["xg_against"]
            away_form = away_xg["xg_for"] - away_xg["xg_against"]

            market_edge = 0.0

            odds = odds_map.get(match["id"], {})
            if odds:
                market_edge = odds.get("home_prob", 0) - odds.get("away_prob", 0)

            # label encoding
            score = match.get("score", {}).get("fullTime", {})
            home_goals = score.get("home", 0)
            away_goals = score.get("away", 0)

            if home_goals > away_goals:
                result = 0
            elif home_goals == away_goals:
                result = 1
            else:
                result = 2

            dataset.append({
                "home_form": home_form,
                "away_form": away_form,
                "market_edge": market_edge,
                "result": result
            })

        except Exception:
            continue

    return pd.DataFrame(dataset)


# debug
if __name__ == "__main__":
    df = asyncio.run(build_dataset())
    print(df.head())
