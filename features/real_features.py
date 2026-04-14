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
# TEAM STATS
# =========================
async def get_team_stats(team_id: int):
    return await fetch(
        f"{FOOTBALL_BASE}/teams/{team_id}",
        headers=headers
    )


# =========================
# ODDS API
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
# INJURY IMPACT (IMPROVED)
# =========================
async def get_injury_impact(team_data: dict):
    """
    Better proxy: squad depth + missing data penalty
    """

    squad = team_data.get("squad", [])

    if not squad:
        return 0.12  # fallback penalty

    squad_size = len(squad)

    # diminishing injury sensitivity
    return min(0.15, max(0.03, 1.0 / (squad_size ** 0.5)))


# =========================
# ODDS PARSER (FIXED)
# =========================
def parse_odds(bookmakers):
    """
    Robust extraction of HOME / AWAY / DRAW odds
    """

    try:
        if not bookmakers:
            return {}

        outcomes = bookmakers[0]["markets"][0]["outcomes"]

        odds = {"home": None, "away": None, "draw": None}

        for o in outcomes:
            name = o.get("name", "").lower()

            if "home" in name:
                odds["home"] = o["price"]

            elif "away" in name:
                odds["away"] = o["price"]

            elif "draw" in name or "tie" in name:
                odds["draw"] = o["price"]

        # fallback safety
        odds["home"] = odds["home"] or 2.0
        odds["away"] = odds["away"] or 2.0
        odds["draw"] = odds["draw"] or 3.2

        return odds

    except Exception:
        return {"home": 2.0, "away": 2.0, "draw": 3.2}


# =========================
# FEATURE ENGINE (CLEAN VERSION)
# =========================
async def build_real_features(match, odds_map=None):

    home_id = match["homeTeam"]["id"]
    away_id = match["awayTeam"]["id"]

    # -------------------------
    # TEAM DATA
    # -------------------------
    home_data, away_data = await asyncio.gather(
        get_team_stats(home_id),
        get_team_stats(away_id)
    )

    # -------------------------
    # INJURY IMPACT
    # -------------------------
    home_injury, away_injury = await asyncio.gather(
        get_injury_impact(home_data),
        get_injury_impact(away_data)
    )

    # -------------------------
    # CLEAN TEAM STRENGTH PROXY
    # -------------------------
    home_strength = len(home_data.get("squad", [])) / 25 if home_data else 0.8
    away_strength = len(away_data.get("squad", [])) / 25 if away_data else 0.8

    # normalize strength
    home_strength = min(1.2, max(0.3, home_strength))
    away_strength = min(1.2, max(0.3, away_strength))

    # -------------------------
    # xG PROXY (STABLE, NOT RANDOM)
    # -------------------------
    home_xg = home_strength * (1.2 - away_strength)
    away_xg = away_strength * (1.2 - home_strength)

    # -------------------------
    # ODDS SIGNAL (FIXED)
    # -------------------------
    odds_data = {}

    if odds_map:
        raw_odds = odds_map.get(match.get("id"), {})
        odds_data = raw_odds

    if isinstance(odds_data, dict) and "home" in odds_data:
        home_odds = odds_data["home"]
        away_odds = odds_data["away"]

        home_prob = 1 / home_odds
        away_prob = 1 / away_odds

        total = home_prob + away_prob
        home_prob /= total
        away_prob /= total

        market_signal = home_prob - away_prob
    else:
        market_signal = 0.0

    # -------------------------
    # FINAL FEATURES (CLEAN + STABLE)
    # -------------------------
    form_diff = home_xg - away_xg
    injury_diff = away_injury - home_injury

    market_edge = market_signal * 0.5

    return [
        float(form_diff),
        float(injury_diff),
        float(market_edge)
    ]
