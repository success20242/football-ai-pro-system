import asyncio
from data.football_api import get_team_stats
from features.market_model import market_vector


# =========================
# SAFE TEAM ID EXTRACTOR
# =========================
def get_team_id(team):
    """
    Supports:
    - {"id": 123, "name": "..."}
    - "Arsenal" (unsupported → fallback)
    """
    if isinstance(team, dict):
        return team.get("id")

    return None


# =========================
# SAFE TEAM STRENGTH (IMPROVED)
# =========================
def team_strength(team_data: dict):
    if not isinstance(team_data, dict):
        return 0.5

    # RapidAPI structure fallback
    if "team" in team_data:
        team_data = team_data.get("team", {})

    squad = team_data.get("squad", [])
    squad_size = len(squad) if isinstance(squad, list) else 0

    # stable scaling
    strength = squad_size / 25 if squad_size else 0.5

    return min(1.5, max(0.2, strength))


# =========================
# SAFE ODDS FETCH
# =========================
def extract_odds(match, odds_map):
    if not isinstance(odds_map, dict):
        return 2.0, 3.2, 2.0

    odds = odds_map.get(match.get("id"), {})

    return (
        float(odds.get("home", 2.0)),
        float(odds.get("draw", 3.2)),
        float(odds.get("away", 2.0))
    )


# =========================
# FINAL FEATURE ENGINE (LOCKED TO 3)
# =========================
async def build_real_features(match, odds_map=None):

    try:
        home_team = match.get("homeTeam")
        away_team = match.get("awayTeam")

        home_id = get_team_id(home_team)
        away_id = get_team_id(away_team)

        # 🚨 If no IDs (like /predict input), fallback to neutral features
        if home_id is None or away_id is None:
            return [0.0, 0.0, 0.0]

        # -------------------------
        # TEAM DATA FETCH (SAFE)
        # -------------------------
        home_data, away_data = await asyncio.gather(
            get_team_stats(home_id),
            get_team_stats(away_id)
        )

        # -------------------------
        # STRENGTH FEATURE
        # -------------------------
        home_strength = team_strength(home_data)
        away_strength = team_strength(away_data)

        strength_diff = home_strength - away_strength

        # -------------------------
        # MARKET FEATURES
        # -------------------------
        home_odds, draw_odds, away_odds = extract_odds(match, odds_map)

        mv = market_vector(home_odds, draw_odds, away_odds)

        market_strength = float(mv.get("strength_diff", 0.0))
        xg_diff = float(mv.get("xg_diff", 0.0))

        # =========================
        # FINAL LOCKED VECTOR (3 ONLY)
        # =========================
        return [
            float(strength_diff),
            market_strength,
            xg_diff
        ]

    except Exception as e:
        print(f"❌ FEATURE ERROR → {e}")
        return [0.0, 0.0, 0.0]
