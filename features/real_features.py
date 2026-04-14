import asyncio
from data.football_api import get_team_stats
from features.market_model import market_vector


# =========================
# SAFE TEAM ID EXTRACTOR
# =========================
def get_team_id(team):
    """
    Handles both formats:
    - {"id": 123, "name": "..."}
    - "Arsenal"
    """

    if isinstance(team, dict):
        return team.get("id")

    # fallback: cannot resolve name → return None
    return None


# =========================
# SAFE TEAM STRENGTH
# =========================
def team_strength(team_data: dict):
    if not isinstance(team_data, dict):
        return 0.5  # safe fallback

    squad = team_data.get("squad", [])
    base = len(squad) if isinstance(squad, list) else 0

    return min(1.5, max(0.2, base / 25))


# =========================
# FINAL FEATURE ENGINE
# =========================
async def build_real_features(match, odds_map=None):

    # -------------------------
    # FIX: SAFE MATCH HANDLING
    # -------------------------
    home_team = match.get("homeTeam")
    away_team = match.get("awayTeam")

    home_id = get_team_id(home_team)
    away_id = get_team_id(away_team)

    # If IDs missing → prevent crash
    if home_id is None or away_id is None:
        return [0.0, 0.0, 0.0, 0.0]

    # -------------------------
    # TEAM DATA FETCH
    # -------------------------
    home_data, away_data = await asyncio.gather(
        get_team_stats(home_id),
        get_team_stats(away_id)
    )

    # -------------------------
    # STRENGTH MODEL
    # -------------------------
    home_strength = team_strength(home_data)
    away_strength = team_strength(away_data)

    strength_diff = home_strength - away_strength

    # -------------------------
    # MARKET DATA (SAFE)
    # -------------------------
    odds = {}
    if isinstance(odds_map, dict):
        odds = odds_map.get(match.get("id"), {}) or {}

    mv = market_vector(
        odds.get("home", 2.0),
        odds.get("draw", 3.2),
        odds.get("away", 2.0)
    )

    # -------------------------
    # FINAL FEATURE VECTOR
    # -------------------------
    return [
        float(strength_diff),
        float(mv.get("strength_diff", 0.0)),
        float(mv.get("xg_diff", 0.0)),
        float(mv.get("market_entropy", 0.0))
    ]
