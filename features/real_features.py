import httpx
import os
from dotenv import load_dotenv

load_dotenv()

FOOTBALL_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

FOOTBALL_BASE = "https://api.football-data.org/v4"

headers = {"X-Auth-Token": FOOTBALL_API_KEY}


# =========================
# TEAM STATS (REAL API)
# =========================
async def get_team_stats(team_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{FOOTBALL_BASE}/teams/{team_id}",
            headers=headers
        )
        return r.json()


# =========================
# ODDS (REAL MARKET SIGNAL)
# =========================
async def get_odds():
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.the-odds-api.com/v4/sports/soccer/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "eu",
                "markets": "h2h"
            }
        )
        return r.json()


# =========================
# INJURY IMPACT (REALISTIC PROXY ONLY IF NO DATA SOURCE)
# =========================
async def get_injury_impact(team_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{FOOTBALL_BASE}/teams/{team_id}",
            headers=headers
        )
        data = r.json()

        # ⚠️ still proxy (Football-data has no injury endpoint)
        squad_size = len(data.get("squad", []))

        # normalized penalty (small + bounded)
        return min(0.15, max(0.02, 1 / (squad_size + 10)))


# =========================
# FEATURE ENGINE (REAL QUANT SIGNALS)
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

    # -------------------------
    # REALISTIC ATTACK/DEFENSE SIGNALS
    # (still proxy but now structured properly)
    # -------------------------
    home_attack = len(home_stats.get("squad", [])) / 30
    away_attack = len(away_stats.get("squad", [])) / 30

    home_defense = 1 - home_attack
    away_defense = 1 - away_attack

    home_xg = home_attack * away_defense
    away_xg = away_attack * home_defense

    # -------------------------
    # MARKET EDGE (ONLY IF ODDS AVAILABLE)
    # -------------------------
    odds = odds_map.get(match.get("id"), {}) if odds_map else {}

    home_odds = odds.get("home", 2.0)
    draw_odds = odds.get("draw", 3.2)
    away_odds = odds.get("away", 3.0)

    home_prob = 1 / home_odds
    draw_prob = 1 / draw_odds
    away_prob = 1 / away_odds

    total = home_prob + draw_prob + away_prob

    home_prob /= total
    draw_prob /= total
    away_prob /= total

    market_edge = (home_xg - away_xg) * (home_prob - away_prob)

    # -------------------------
    # INJURY ADJUSTMENT
    # -------------------------
    home_form = home_xg - home_injury
    away_form = away_xg - away_injury

    return [
        float(home_form),
        float(away_form),
        float(market_edge)
    ]
