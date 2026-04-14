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

    fixtures_data = await get_fixtures(competition)
    odds_data = await get_odds()

    fixtures = fixtures_data.get("matches", [])[:limit]

    odds_map = build_odds_map(odds_data)

    dataset = []

    for match in fixtures:

        try:
            home_id = match["homeTeam"]["id"]
            away_id = match["awayTeam"]["id"]

            home_xg = await get_team_xg(home_id)
            away_xg = await get_team_xg(away_id)

            # -------------------------
            # REAL xG FEATURES
            # -------------------------
            home_form = home_xg["xg_for"] - home_xg["xg_against"]
            away_form = away_xg["xg_for"] - away_xg["xg_against"]

            # -------------------------
            # ODDS FEATURES
            # -------------------------
            match_odds = odds_map.get(match["id"], {})

            home_odds = match_odds.get("home", 2.0)
            draw_odds = match_odds.get("draw", 3.2)
            away_odds = match_odds.get("away", 3.0)

            market_edge = (1 / home_odds) - (1 / away_odds)

            # -------------------------
            # LABEL (historical result)
            # -------------------------
            score = match.get("score", {}).get("fullTime", {})

            if not score:
                continue

            if score["home"] > score["away"]:
                result = 0
            elif score["home"] == score["away"]:
                result = 1
            else:
                result = 2

            dataset.append({
                "home_form": home_form,
                "away_form": away_form,
                "market_edge": market_edge,
                "odds_home": home_odds,
                "odds_draw": draw_odds,
                "odds_away": away_odds,
                "result": result
            })

        except Exception:
            continue

    return pd.DataFrame(dataset)
