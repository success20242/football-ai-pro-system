import asyncio
from data.football_api import get_team_stats
from features.market_model import market_vector


# =========================
# TEAM STRENGTH (ELO-LITE)
# =========================
def team_strength(team_data: dict):
    squad = team_data.get("squad", [])
    base = len(squad)

    return min(1.5, max(0.2, base / 25))


# =========================
# FINAL FEATURE ENGINE
# =========================
async def build_real_features(match, odds_map=None):

    home_id = match["homeTeam"]["id"]
    away_id = match["awayTeam"]["id"]

    home_data, away_data = await asyncio.gather(
        get_team_stats(home_id),
        get_team_stats(away_id)
    )

    home_strength = team_strength(home_data)
    away_strength = team_strength(away_data)

    strength_diff = home_strength - away_strength

    odds = odds_map.get(match.get("id"), {}) if odds_map else {}

    mv = market_vector(
        odds.get("home", 2.0),
        odds.get("draw", 3.2),
        odds.get("away", 2.0)
    )

    return [
        strength_diff,
        mv["strength_diff"],
        mv["xg_diff"],
        mv["market_entropy"]
    ]
