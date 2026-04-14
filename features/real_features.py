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
# TEAM STATS
# =========================
async def get_team_stats(team_id: int):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{FOOTBALL_BASE}/teams/{team_id}",
            headers=headers
        )
        return r.json() if r.status_code == 200 else {}


# =========================
# ODDS (REAL MARKET SIGNAL)
# =========================
async def get_odds():
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            "https://api.the-odds-api.com/v4/sports/soccer_epl/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "eu",
                "markets": "h2h",
                "oddsFormat": "decimal"
            }
        )
        return r.json() if r.status_code == 200 else []


# =========================
# INJURY IMPACT (PROXY)
# =========================
async def get_injury_impact(team_id: int):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{FOOTBALL_BASE}/teams/{team_id}",
            headers=headers
        )
        data = r.json() if r.status_code == 200 else {}

    squad_size = len(data.get("squad", []))

    return min(0.15, max(0.02, 1 / (squad_size + 10)))


# =========================
# ODDS MAP BUILDER
# =========================
def build_odds_map(odds_data):
    """
    Converts odds API response → {match_id: {home, draw, away}}
    """
    odds_map = {}

    for game in odds_data:
        match_id = game.get("id")

        bookmakers = game.get("bookmakers", [])
        if not bookmakers:
            continue

        outcomes = bookmakers[0]["markets"][0]["outcomes"]

        odds_map[match_id] = {
            "home": outcomes[0]["price"],
            "away": outcomes[1]["price"],
            "draw": outcomes[2]["price"] if len(outcomes) > 2 else 3.2
        }

    return odds_map


# =========================
# FEATURE ENGINE (REAL QUANT CORE)
# =========================
async def build_real_features(match, odds_map=None):

    home_id = match["homeTeam"]["id"]
    away_id = match["awayTeam"]["id"]

    home_stats, away_stats = await asyncio.gather(
        get_team_stats(home_id),
        get_team_stats(away_id)
    )

    home_injury, away_injury = await asyncio.gather(
        get_injury_impact(home_id),
        get_injury_impact(away_id)
    )

    # =========================
    # xG PROXY (STRUCTURED)
    # =========================
    home_attack = len(home_stats.get("squad", [])) / 30
    away_attack = len(away_stats.get("squad", [])) / 30

    home_defense = 1 - home_attack
    away_defense = 1 - away_attack

    home_xg = home_attack * away_defense
    away_xg = away_attack * home_defense

    # =========================
    # MARKET SIGNAL (REAL ODDS)
    # =========================
    odds = odds_map.get(match.get("id"), {}) if odds_map else {}

    home_odds = odds.get("home", 2.0)
    away_odds = odds.get("away", 2.0)

    home_prob = 1 / home_odds
    away_prob = 1 / away_odds

    total = home_prob + away_prob
    home_prob /= total
    away_prob /= total

    market_edge = (home_xg - away_xg) * (home_prob - away_prob)

    # =========================
    # INJURY ADJUSTED FORM
    # =========================
    home_form = home_xg - home_injury
    away_form = away_xg - away_injury

    return [
        float(home_form),
        float(away_form),
        float(market_edge)
    ]
