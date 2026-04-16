import pandas as pd
from data.football_api import get_fixtures
from data.odds_api import get_odds
from data.xg_api import get_team_xg


# =========================
# LABEL ENCODING
# =========================
def label_result(home_goals, away_goals):
    if home_goals > away_goals:
        return 1
    elif home_goals < away_goals:
        return 0
    return 2


# =========================
# SAFE VALUE
# =========================
def safe_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0


# =========================
# BUILD DATASET (IMPROVED)
# =========================
async def build_dataset(competition="PL"):

    fixtures = await get_fixtures(competition)
    odds_data = await get_odds()

    # optional: build quick odds lookup
    odds_map = {
        o.get("id"): o
        for o in odds_data or []
        if isinstance(o, dict)
    }

    rows = []

    for match in fixtures.get("matches", []):

        try:
            home_id = match["homeTeam"]["id"]
            away_id = match["awayTeam"]["id"]

            home_xg = await get_team_xg(home_id) or {}
            away_xg = await get_team_xg(away_id) or {}

            # =========================
            # REAL xG FEATURES
            # =========================
            home_form = safe_float(home_xg.get("xg_for")) - safe_float(home_xg.get("xg_against"))
            away_form = safe_float(away_xg.get("xg_for")) - safe_float(away_xg.get("xg_against"))

            momentum = home_form - away_form

            # =========================
            # MARKET SIGNAL (REAL FIX)
            # =========================
            match_odds = odds_map.get(match.get("id"), {}) or {}

            home_odds = safe_float(match_odds.get("home", 2.0))
            draw_odds = safe_float(match_odds.get("draw", 3.2))
            away_odds = safe_float(match_odds.get("away", 2.0))

            # implied probabilities
            p_home = 1 / home_odds if home_odds > 0 else 0.33
            p_draw = 1 / draw_odds if draw_odds > 0 else 0.34
            p_away = 1 / away_odds if away_odds > 0 else 0.33

            market_strength = p_home - p_away

            # =========================
            # LABEL
            # =========================
            score = match.get("score", {}).get("fullTime", {})
            if not score:
                continue

            y = label_result(
                score.get("home", 0),
                score.get("away", 0)
            )

            # =========================
            # FINAL ROW
            # =========================
            rows.append({
                "home_form": home_form,
                "away_form": away_form,
                "momentum": momentum,
                "market_edge": market_strength,
                "odds_home": home_odds,
                "odds_draw": draw_odds,
                "odds_away": away_odds,
                "result": y
            })

        except Exception:
            continue

    return pd.DataFrame(rows)
