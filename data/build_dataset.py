import pandas as pd
from data.football_api import get_fixtures
from data.odds_api import get_odds
from data.xg_api import get_team_xg


def label_result(home_goals, away_goals):
    if home_goals > away_goals:
        return 1
    elif home_goals < away_goals:
        return 0
    return 2


async def build_dataset(competition="PL"):

    fixtures = await get_fixtures(competition)
    odds = await get_odds()

    rows = []

    for match in fixtures.get("matches", []):

        try:
            home_id = match["homeTeam"]["id"]
            away_id = match["awayTeam"]["id"]

            home_xg = await get_team_xg(home_id)
            away_xg = await get_team_xg(away_id)

            # -------------------------
            # FEATURES (REAL QUANT SIGNALS)
            # -------------------------
            home_form = home_xg["xg_for"] - home_xg["xg_against"]
            away_form = away_xg["xg_for"] - away_xg["xg_against"]
            momentum = home_form - away_form

            market_edge = momentum * 0.15

            # -------------------------
            # LABEL (RESULT)
            # -------------------------
            score = match.get("score", {}).get("fullTime", {})
            if not score:
                continue

            y = label_result(
                score.get("home", 0),
                score.get("away", 0)
            )

            rows.append({
                "home_form": home_form,
                "away_form": away_form,
                "market_edge": market_edge,
                "result": y
            })

        except Exception:
            continue

    return pd.DataFrame(rows)
