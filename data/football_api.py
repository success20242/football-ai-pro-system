import os
import httpx
from dotenv import load_dotenv

load_dotenv()

# =========================
# API KEYS
# =========================
FD_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")  # football-data.org
RAPID_API_KEY = os.getenv("FOOTBALL_API_KEY")   # API-Football
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

FD_BASE = "https://api.football-data.org/v4"
RAPID_BASE = "https://api-football-v1.p.rapidapi.com/v3"


# =========================
# HEADERS
# =========================
FD_HEADERS = {"X-Auth-Token": FD_API_KEY} if FD_API_KEY else {}
RAPID_HEADERS = {
    "X-RapidAPI-Key": RAPID_API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
} if RAPID_API_KEY else {}


# =========================
# GENERIC FETCH
# =========================
async def fetch(url: str, headers=None, params=None):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, headers=headers, params=params)

            if r.status_code != 200:
                return None

            return r.json()

    except Exception:
        return None


# =========================
# NORMALIZERS
# =========================
def normalize_fd_match(m):
    """football-data.org format → unified"""
    try:
        return {
            "id": m["id"],
            "league": m["competition"]["name"],
            "timestamp": m["utcDate"],
            "status": m["status"],

            "homeTeam": {
                "id": m["homeTeam"]["id"],
                "name": m["homeTeam"]["name"]
            },
            "awayTeam": {
                "id": m["awayTeam"]["id"],
                "name": m["awayTeam"]["name"]
            }
        }
    except Exception:
        return None


def normalize_rapid_match(m):
    """API-Football format → unified"""
    try:
        return {
            "id": m["fixture"]["id"],
            "league": m["league"]["name"],
            "timestamp": m["fixture"]["date"],
            "status": m["fixture"]["status"]["short"],

            "homeTeam": {
                "id": m["teams"]["home"]["id"],
                "name": m["teams"]["home"]["name"]
            },
            "awayTeam": {
                "id": m["teams"]["away"]["id"],
                "name": m["teams"]["away"]["name"]
            }
        }
    except Exception:
        return None


# =========================
# LIVE MATCHES (SMART HYBRID)
# =========================
async def get_live_matches():
    """
    Try API-Football first (better live data),
    fallback to football-data.org
    """

    # -------------------------
    # 1. TRY RAPID API (BEST)
    # -------------------------
    if RAPID_API_KEY:
        data = await fetch(
            f"{RAPID_BASE}/fixtures",
            headers=RAPID_HEADERS,
            params={"live": "all"}
        )

        if data and "response" in data:
            matches = [
                normalize_rapid_match(m)
                for m in data["response"]
            ]

            matches = [m for m in matches if m]

            if matches:
                return {"matches": matches}

    # -------------------------
    # 2. FALLBACK: FOOTBALL-DATA
    # -------------------------
    if FD_API_KEY:
        data = await fetch(
            f"{FD_BASE}/matches",
            headers=FD_HEADERS,
            params={"status": "LIVE"}
        )

        if data and "matches" in data:
            matches = [
                normalize_fd_match(m)
                for m in data["matches"]
            ]

            matches = [m for m in matches if m]

            return {"matches": matches}

    return {"matches": []}


# =========================
# UPCOMING MATCHES (FALLBACK)
# =========================
async def get_upcoming_matches():

    # try Rapid first
    if RAPID_API_KEY:
        data = await fetch(
            f"{RAPID_BASE}/fixtures",
            headers=RAPID_HEADERS,
            params={"next": 10}
        )

        if data and "response" in data:
            matches = [normalize_rapid_match(m) for m in data["response"]]
            return {"matches": [m for m in matches if m]}

    # fallback football-data
    if FD_API_KEY:
        data = await fetch(
            f"{FD_BASE}/matches",
            headers=FD_HEADERS
        )

        if data and "matches" in data:
            matches = [normalize_fd_match(m) for m in data["matches"]]
            return {"matches": [m for m in matches if m]}

    return {"matches": []}


# =========================
# TEAM STATS (UNIFIED)
# =========================
async def get_team_stats(team_id: int):

    if FD_API_KEY:
        data = await fetch(
            f"{FD_BASE}/teams/{team_id}",
            headers=FD_HEADERS
        )
        return data or {}

    if RAPID_API_KEY:
        data = await fetch(
            f"{RAPID_BASE}/teams",
            headers=RAPID_HEADERS,
            params={"id": team_id}
        )
        return data or {}

    return {}


# =========================
# ODDS (UNCHANGED BUT ALIGNED)
# =========================
async def get_match_odds(sport="soccer_epl"):

    if not ODDS_API_KEY:
        return []

    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"

    return await fetch(
        url,
        headers={},
        params={
            "apiKey": ODDS_API_KEY,
            "regions": "eu",
            "markets": "h2h"
        }
    ) or []
