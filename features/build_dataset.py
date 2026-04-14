import asyncio
import pandas as pd

from data.football_api import get_fixtures
from data.odds_api import get_odds
from data.xg_api import get_team_xg


# =========================
# RESULT MAPPING (REAL LABELS)
# =========================
def get_result_label(home_goals, away_goals):
    if home_goals > away_goals:
        return 0  # home win
    elif home_goals == away_goals:
        return 1  # draw
    else:
        return 2  # away win


# =========================
# ODDS MAPPING
# =========================
def build_odds_map(odds_data):
    """
    Converts odds API response into:
    { match_id: {home, draw, away} }
    """
    odds_map = {}

    for match in odds_data:
        try:
            bookmakers = match.get("bookmakers", [])
            if not bookmakers:
                continue

            outcomes = bookmakers[0]["markets"][0]["outcomes"]

            home = next(o for o in outcomes if o["name"] != "Draw")
            draw = next(o for o in outcomes if o["name"] == "Draw")
            away = next(o for o in outcomes if o["name"] != home["name"])

            odds_map[match["id"]] = {
                "home": home["price"],
                "draw": draw["price"],
                "away": away["price"]
            }

        except Exception:
            continue

    return odds_map


# =========================
# FEATURE BUILDER
# =========================
async def build_match_features(match, odds_map):
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
    # MARKET EDGE (ODDS)
    # -------------------------
    odds = odds_map.get(match["id"], None)

    if odds:
        home_prob = 1 / odds["home"]
        draw_prob = 1 / odds["draw"]
        away_prob = 1 / odds["away"]

        total = home_prob + draw_prob + away_prob

        home_prob /= total
        away_prob /= total

        market_edge = home_prob - away_prob
    else:
        market_edge = 0.0

    return [
        float(home_form),
        float(away_form),
        float(market_edge)
    ]


# =========================
# MAIN DATASET BUILDER
# =========================
async def build_dataset(competition="PL", limit=200):
    """
    Builds REAL ML dataset:
    xG + odds + historical results
    """

    print("📊 Fetching historical matches...")

    fixtures = await get_fixtures(competition)
    odds_data = await get_odds()

    matches = fixtures.get("matches", [])[:limit]

    odds_map = build_odds_map(odds_data)

    dataset = []

    print(f"⚙️ Processing {len(matches)} matches...")

    for match in matches:

        try:
            score = match.get("score", {})
            full_time = score.get("fullTime", {})

            home_goals = full_time.get("home")
            away_goals = full_time.get("away")

            # skip unfinished matches
            if home_goals is None or away_goals is None:
                continue

            features = await build_match_features(match, odds_map)

            label = get_result_label(home_goals, away_goals)

            dataset.append({
                "home_form": features[0],
                "away_form": features[1],
                "market_edge": features[2],
                "result": label
            })

        except Exception:
            continue

    df = pd.DataFrame(dataset)

    print(f"✅ Dataset built: {len(df)} samples")

    return df
