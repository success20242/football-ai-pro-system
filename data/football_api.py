import os
import asyncio
import logging
import httpx
from dotenv import load_dotenv

from core.rate_limiter import acquire_slot

load_dotenv()

logger = logging.getLogger("football-api")
logging.basicConfig(level=logging.INFO)

# =========================
# API KEYS
# =========================
FD_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")

FD_BASE = "https://api.football-data.org/v4"

FD_HEADERS = {"X-Auth-Token": FD_API_KEY} if FD_API_KEY else {}

client = httpx.AsyncClient(timeout=10)


# =========================
# FETCH (SAFE)
# =========================
async def fetch(url: str, params=None, retries=2):

    for attempt in range(retries + 1):

        try:
            allowed = await acquire_slot()
            if not allowed:
                await asyncio.sleep(0.3)

            r = await client.get(url, headers=FD_HEADERS, params=params)

            if r.status_code == 200:
                return r.json()

            if r.status_code == 429:
                await asyncio.sleep(1.5 * (attempt + 1))
                continue

            return None

        except Exception:
            await asyncio.sleep(0.5)

    return None


# =========================
# NORMALIZE
# =========================
def normalize_match(m):
    try:
        return {
            "id": m.get("id"),
            "league": m.get("competition", {}).get("name"),
            "timestamp": m.get("utcDate"),
            "status": m.get("status"),
            "homeTeam": {
                "id": m.get("homeTeam", {}).get("id"),
                "name": m.get("homeTeam", {}).get("name")
            },
            "awayTeam": {
                "id": m.get("awayTeam", {}).get("id"),
                "name": m.get("awayTeam", {}).get("name")
            }
        }
    except:
        return None


# =========================
# LIVE MATCHES
# =========================
async def get_live_matches():

    if not FD_API_KEY:
        return {"matches": []}

    data = await fetch(
        f"{FD_BASE}/matches",
        params={"status": "LIVE"}
    )

    matches = data.get("matches", []) if data else []

    cleaned = [normalize_match(m) for m in matches]
    return {"matches": [m for m in cleaned if m]}


# =========================
# UPCOMING MATCHES
# =========================
async def get_upcoming_matches():

    if not FD_API_KEY:
        return {"matches": []}

    data = await fetch(f"{FD_BASE}/matches")

    matches = data.get("matches", []) if data else []

    cleaned = [normalize_match(m) for m in matches]
    return {"matches": [m for m in cleaned if m]}


# =========================
# TEAM STATS
# =========================
async def get_team_stats(team_id: int):

    if not team_id or not FD_API_KEY:
        return {}

    data = await fetch(f"{FD_BASE}/teams/{team_id}")

    return data if isinstance(data, dict) else {}
