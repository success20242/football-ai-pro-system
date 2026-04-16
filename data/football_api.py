import os
import asyncio
import logging
import random
import httpx
from dotenv import load_dotenv

from core.rate_limiter import acquire_slot

load_dotenv()

logger = logging.getLogger("football-api")
logging.basicConfig(level=logging.INFO)

# =========================
# API CONFIG
# =========================
FD_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
FD_BASE = "https://api.football-data.org/v4"

FD_HEADERS = {
    "X-Auth-Token": FD_API_KEY
} if FD_API_KEY else {}

# =========================
# HTTP CLIENT (FIXED)
# =========================
client = httpx.AsyncClient(timeout=15)

# simple in-memory cache (IMPORTANT FIX)
TEAM_CACHE = {}


# =========================
# SAFE FETCH (IMPROVED)
# =========================
async def fetch(url: str, params=None, retries=3):

    for attempt in range(retries):

        try:
            await acquire_slot()

            r = await client.get(
                url,
                headers=FD_HEADERS,
                params=params
            )

            if r.status_code == 200:
                return r.json()

            if r.status_code == 429:
                wait = (1.5 * (attempt + 1)) + random.uniform(0.2, 1.0)
                logger.warning(f"Rate limited → retrying in {wait:.2f}s")
                await asyncio.sleep(wait)
                continue

            logger.warning(f"API error {r.status_code} → {url}")
            return None

        except Exception as e:
            logger.error(f"Fetch exception: {e}")
            await asyncio.sleep(0.5 + random.random())

    return None


# =========================
# NORMALIZE MATCH
# =========================
def normalize_match(m):

    if not isinstance(m, dict):
        return None

    try:
        return {
            "id": m.get("id"),
            "league": (m.get("competition") or {}).get("name"),
            "timestamp": m.get("utcDate"),
            "status": m.get("status"),

            "homeTeam": {
                "id": (m.get("homeTeam") or {}).get("id"),
                "name": (m.get("homeTeam") or {}).get("name")
            },

            "awayTeam": {
                "id": (m.get("awayTeam") or {}).get("id"),
                "name": (m.get("awayTeam") or {}).get("name")
            }
        }

    except Exception as e:
        logger.warning(f"Normalize error: {e}")
        return None


# =========================
# LIVE MATCHES
# =========================
async def get_live_matches():

    if not FD_API_KEY:
        logger.error("Missing FOOTBALL_DATA_API_KEY")
        return {"matches": []}

    data = await fetch(f"{FD_BASE}/matches", params={"status": "LIVE"})

    if not data:
        return {"matches": []}

    matches = data.get("matches", []) if isinstance(data, dict) else []

    return {"matches": [normalize_match(m) for m in matches if normalize_match(m)]}


# =========================
# UPCOMING MATCHES
# =========================
async def get_upcoming_matches():

    if not FD_API_KEY:
        return {"matches": []}

    data = await fetch(f"{FD_BASE}/matches")

    if not data:
        return {"matches": []}

    matches = data.get("matches", []) if isinstance(data, dict) else []

    return {"matches": [normalize_match(m) for m in matches if normalize_match(m)]}


# =========================
# TEAM STATS (CACHED FIX)
# =========================
async def get_team_stats(team_id: int):

    if not team_id or not FD_API_KEY:
        return {}

    # CACHE HIT
    if team_id in TEAM_CACHE:
        return TEAM_CACHE[team_id]

    data = await fetch(f"{FD_BASE}/teams/{team_id}")

    if isinstance(data, dict):
        TEAM_CACHE[team_id] = data

    return data if isinstance(data, dict) else {}


# =========================
# CLEAN SHUTDOWN (IMPORTANT FIX)
# =========================
async def close_client():
    await client.aclose()
