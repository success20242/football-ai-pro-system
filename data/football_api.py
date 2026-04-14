import os
import httpx
from dotenv import load_dotenv

load_dotenv()

FOOTBALL_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

FOOTBALL_BASE = "https://api.football-data.org/v4"


headers = {
    "X-Auth-Token": FOOTBALL_API_KEY
}


# =========================
# SAFE REQUEST WRAPPER
# =========================
async def fetch(url: str, params=None, use_odds=False):
    try:
        async with httpx.AsyncClient(timeout=15) as client:

            h = headers.copy()

            # odds API uses different auth system
            if use_odds:
                h = {}

            r = await client.get(url, headers=h, params=params)

            if r.status_code != 200:
                print(f"⚠️ API Error {r.status_code}: {url}")
                return {}

            return r.json()

    except Exception as e:
        print(f"❌ Request failed: {e}")
        return {}


# =========================
# LIVE MATCHES (REAL TIME)
# =========================
async def get_live_matches():
    return await fetch(
        f"{FOOTBALL_BASE}/matches",
        params={"status": "LIVE"}
    )


# =========================
# FIXTURES (HISTORICAL BUILDING BLOCK)
# =========================
async def get_fixtures(competition="PL"):
    return await fetch(
        f"{FOOTBALL_BASE}/competitions/{competition}/matches"
    )


# =========================
# TEAM STATS (xG PROXY LAYER)
# =========================
async def get_team_stats(team_id: int):
    return await fetch(f"{FOOTBALL_BASE}/teams/{team_id}")


# =========================
# 🟢 ODDS DATA (CRITICAL NEW LAYER)
# =========================
async def get_match_odds(sport="soccer_epl"):
    """
    Real odds feed (The Odds API)
    """
    if not ODDS_API_KEY:
        print("⚠️ Missing ODDS_API_KEY")
        return {}

    url = "https://api.the-odds-api.com/v4/sports/{}/odds".format(sport)

    return await fetch(
        url,
        params={
            "apiKey": ODDS_API_KEY,
            "regions": "eu",
            "markets": "h2h"
        },
        use_odds=True
    )


# =========================
# 🧠 NORMALIZED MATCH OUTPUT (IMPORTANT FOR ML)
# =========================
def normalize_match(match: dict):
    """
    Converts API response into ML-ready structure
    """

    try:
        return {
            "match_id": match.get("id"),
            "home_team": match["homeTeam"]["name"],
            "away_team": match["awayTeam"]["name"],
            "home_id": match["homeTeam"]["id"],
            "away_id": match["awayTeam"]["id"],
            "status": match.get("status")
        }
    except Exception:
        return None
