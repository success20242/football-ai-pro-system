import asyncio
import pandas as pd

from data.football_api import get_fixtures
from data.xg_api import get_team_xg
from data.odds_api import get_odds
from utils.odds_utils import build_odds_map


# =========================
# SAFE FEATURE NORMALIZER
# =========================
def safe_div(a, b):
    return a / b if b else 0.0


# =========================
# BUILD REAL TRAINING DATASET (UPGRADED)
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

            # -------------------------
            # xG DATA
            # -------------------------
            home_xg = await get_team_xg(home_id)
            away_xg = await get_team_xg(away_id)

            home_attack = home_xg.get("xg_for", 0)
            home_def = home_xg.get("xg_against", 0)

            away_attack = away_xg.get("xg_for", 0)
            away_def = away_xg.get("xg_against", 0)

            # -------------------------
            # NORMALIZED xG FEATURES
            # -------------------------
            home_form = safe_div(home_attack - home_def, max(home_attack + home_def, 1))
            away_form = safe_div(away_attack - away_def, max(away_attack + away_def, 1))

            xg_diff = home_form - away_form

            # -------------------------
            # ODDS FEATURES
            # -------------------------
            match_odds = odds_map.get(match["id"], {})

            home_odds = match_odds.get("home", 2.0)
            draw_odds = match_odds.get("draw", 3.2)
            away_odds = match_odds.get("away", 3.0)

            # implied probabilities
            h = safe_div(1, home_odds)
            d = safe_div(1, draw_odds)
            a = safe_div(1, away_odds)

            total = h + d + a if (h + d + a) > 0 else 1

            h, d, a = h / total, d / total, a / total

            market_edge = h - a
            draw_pressure = d

            # -------------------------
            # LABEL (CLEAN)
            # -------------------------
            score = match.get("score", {}).get("fullTime", {})

            if not score:
                continue

            home_goals = score.get("home", 0)
            away_goals = score.get("away", 0)

            # binary target (better for stability)
            if home_goals > away_goals:
                result = 1
            else:
                result = 0

            # -------------------------
            # FINAL ROW
            # -------------------------
            dataset.append({
                # xG signals
                "home_form": home_form,
                "away_form": away_form,
                "xg_diff": xg_diff,

                # market signals
                "market_edge": market_edge,
                "draw_pressure": draw_pressure,

                # raw odds
                "odds_home": home_odds,
                "odds_draw": draw_odds,
                "odds_away": away_odds,

                # label
                "result": result
            })

        except Exception:
            continue

    return pd.DataFrame(dataset)
