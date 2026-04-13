import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

FOOTBALL_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

FOOTBALL_BASE = "https://api.football-data.org/v4"


headers = {
    "X-Auth-Token": FOOTBALL_API_KEY
}


# =========================
# 1. TEAM STATS (proxy for xG)
# =========================
async def get_team_stats(team_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{FOOTBALL_BASE}/teams/{team_id}",
            headers=headers
        )
        return r.json()


# =========================
# 2. ODDS DATA (market signal)
# =========================
async def get_match_odds():
    """
    Replace endpoint with your odds provider (OddsAPI, Bet365, etc.)
    """
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.the-odds-api.com/v4/sports/soccer/odds",
            params={"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h"}
        )
        return r.json()


# =========================
# 3. INJURY IMPACT (simplified)
# =========================
async def get_injury_impact(team_id: int):
    """
    Placeholder — real systems use paid injury feeds (Transfermarkt, API-Football)
    """
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                f"{FOOTBALL_BASE}/teams/{team_id}",
                headers=headers
            )
            data = r.json()

            # simulate injury strength loss
            squad_size = len(data.get("squad", []))
            injury_factor = min(0.2, squad_size / 200)

            return injury_factor

        except Exception:
            return 0.1


# =========================
# 4. FINAL FEATURE BUILDER
# =========================
async def build_real_features(match):
    """
    Produces ML-ready feature vector
    """

    home_id = match["homeTeam"]["id"]
    away_id = match["awayTeam"]["id"]

    home_stats = await get_team_stats(home_id)
    away_stats = await get_team_stats(away_id)

    home_injury = await get_injury_impact(home_id)
    away_injury = await get_injury_impact(away_id)

    # -------------------------
    # xG proxy (goals for / defensive weakness)
    # -------------------------
    home_attack = len(home_stats.get("squad", [])) * 0.05
    away_attack = len(away_stats.get("squad", [])) * 0.05

    home_defense = 1 - home_attack
    away_defense = 1 - away_attack

    home_xg = home_attack * away_defense
    away_xg = away_attack * home_defense

    # -------------------------
    # MARKET EDGE (odds-driven)
    # -------------------------
    # simplified placeholder until full odds mapping
    market_edge = (home_xg - away_xg) * 0.15

    # -------------------------
    # INJURY ADJUSTED FORM
    # -------------------------
    home_form = home_xg - home_injury
    away_form = away_xg - away_injury

    return [
        float(home_form),
        float(away_form),
        float(market_edge)
    ]
