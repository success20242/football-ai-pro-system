import asyncio
import re
from data.football_api import get_team_stats
from features.market_model import market_vector


# =========================
# TEAM NAME NORMALIZER (IMPROVED)
# =========================
def normalize_team(name: str):
    if not name:
        return ""

    name = name.lower()

    # remove special characters
    name = re.sub(r'[^a-z0-9 ]', '', name)

    # remove common suffixes
    words = name.split()
    words = [w for w in words if w not in ["fc", "cf", "afc", "club"]]

    return " ".join(words)


# =========================
# SAFE TEAM ID EXTRACTOR
# =========================
def get_team_id(team):
    if isinstance(team, dict):
        return team.get("id")
    return None


# =========================
# TEAM STRENGTH (UPGRADED)
# =========================
def team_strength(team_data: dict):
    if not isinstance(team_data, dict):
        return 0.5

    stats = team_data.get("statistics", {})

    wins = stats.get("wins", 0)
    games = stats.get("played", 0)

    if games == 0:
        return 0.5

    return wins / games


# =========================
# ODDS EXTRACTOR (DEBUG ENABLED)
# =========================
def extract_odds(match, odds_map):

    if not isinstance(odds_map, dict):
        return 2.0, 3.2, 2.0

    home_name = normalize_team(
        match.get("homeTeam", {}).get("name")
    )
    away_name = normalize_team(
        match.get("awayTeam", {}).get("name")
    )

    match_key = f"{home_name}_{away_name}"

    if match_key not in odds_map:
        print(f"⚠️ ODDS NOT FOUND: {match_key}")

    odds = odds_map.get(match_key, {})

    return (
        float(odds.get("home", 2.0)),
        float(odds.get("draw", 3.2)),
        float(odds.get("away", 2.0))
    )


# =========================
# FINAL FEATURE ENGINE (FIXED)
# =========================
async def build_real_features(match, odds_map=None):

    try:
        if not isinstance(match, dict):
            return [0.0, 0.0, 0.0, 0.0]

        home_team = match.get("homeTeam")
        away_team = match.get("awayTeam")

        home_id = get_team_id(home_team)
        away_id = get_team_id(away_team)

        # -------------------------
        # TEAM DATA FETCH
        # -------------------------
        if home_id and away_id:
            try:
                home_data, away_data = await asyncio.gather(
                    get_team_stats(home_id),
                    get_team_stats(away_id)
                )
            except Exception:
                home_data, away_data = {}, {}
        else:
            home_data, away_data = {}, {}

        # -------------------------
        # TEAM STRENGTH
        # -------------------------
        home_strength = team_strength(home_data)
        away_strength = team_strength(away_data)

        strength_diff = home_strength - away_strength

        # -------------------------
        # ODDS EXTRACTION
        # -------------------------
        home_odds, draw_odds, away_odds = extract_odds(match, odds_map)

        # implied probabilities
        try:
            home_prob = 1 / home_odds if home_odds else 0.33
            draw_prob = 1 / draw_odds if draw_odds else 0.33
            away_prob = 1 / away_odds if away_odds else 0.33

            total = home_prob + draw_prob + away_prob

            home_prob /= total
            draw_prob /= total
            away_prob /= total

        except Exception:
            home_prob, draw_prob, away_prob = 0.33, 0.34, 0.33

        # -------------------------
        # MARKET FEATURES
        # -------------------------
        mv = market_vector(home_odds, draw_odds, away_odds)
        market_strength = float(mv.get("strength_diff", 0.0))

        # -------------------------
        # UNIQUE MATCH FEATURE (IMPORTANT)
        # -------------------------
        match_id = match.get("id", 0)
        match_uniqueness = (match_id % 1000) / 1000

        # -------------------------
        # FINAL FEATURE VECTOR
        # -------------------------
        return [
            round(float(home_prob - away_prob), 4),   # odds signal
            round(float(strength_diff), 4),           # team strength
            round(float(market_strength), 4),         # market edge
            round(float(match_uniqueness), 4)         # uniqueness
        ]

    except Exception as e:
        print(f"❌ FEATURE ERROR → {e}")
        return [0.0, 0.0, 0.0, 0.0]
