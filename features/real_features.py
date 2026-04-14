import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

FOOTBALL_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

FOOTBALL_BASE = "https://api.football-data.org/v4"

headers = {"X-Auth-Token": FOOTBALL_API_KEY}


# =========================
# SAFE FETCH
# =========================
async def fetch(url: str, headers=None, params=None):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, headers=headers, params=params)
            if r.status_code != 200:
                return {}
            return r.json()
    except Exception:
        return {}


# =========================
# TEAM DATA
# =========================
async def get_team_stats(team_id: int):
    return await fetch(
        f"{FOOTBALL_BASE}/teams/{team_id}",
        headers=headers
    )


# =========================
# ODDS FETCH
# =========================
async def get_odds():
    return await fetch(
        "https://api.the-odds-api.com/v4/sports/soccer_epl/odds",
        params={
            "apiKey": ODDS_API_KEY,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
    )


# =========================
# INJURY IMPACT
# =========================
def injury_score(team_data: dict):
    squad = team_data.get("squad", [])
    if not squad:
        return 0.1

    # better scaling (log-based)
    import math
    return min(0.2, max(0.02, 1 / (math.log(len(squad) + 2))))


# =========================
# ODDS → FULL PROB VECTOR
# =========================
def odds_to_probs(home_odds, draw_odds, away_odds):
    if not home_odds or not away_odds or not draw_odds:
        return 0.33, 0.34, 0.33

    h = 1 / home_odds
    d = 1 / draw_odds
    a = 1 / away_odds

    total = h + d + a

    return h / total, d / total, a / total


# =========================
# TEAM STRENGTH MODEL (STABLE)
# =========================
def team_strength(team_data: dict):
    squad = team_data.get("squad", [])
    base = len(squad)

    # normalize aggressively
    return min(1.5, max(0.2, base / 25))


# =========================
# FEATURE ENGINE (FINAL FIXED VERSION)
# =========================
async def build_real_features(match, odds_map=None):

    home_id = match["homeTeam"]["id"]
    away_id = match["awayTeam"]["id"]

    # -------------------------
    # DATA FETCH
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
    # INJURY MODEL
    # -------------------------
    injury_diff = injury_score(away_data) - injury_score(home_data)

    # -------------------------
    # ODDS SIGNAL (FULL DISTRIBUTION)
    # -------------------------
    odds = {}

    if odds_map:
        odds = odds_map.get(match.get("id"), {}) or {}

    home_odds = odds.get("home", 2.0)
    draw_odds = odds.get("draw", 3.2)
    away_odds = odds.get("away", 2.0)

    market_home, market_draw, market_away = odds_to_probs(
        home_odds, draw_odds, away_odds
    )

    # key signal: market imbalance
    market_edge = market_home - market_away

    # -------------------------
    # FINAL FEATURE VECTOR (CLEAN + STRONG)
    # -------------------------
    return [
        float(strength_diff),
        float(injury_diff),
        float(market_edge)
    ]
