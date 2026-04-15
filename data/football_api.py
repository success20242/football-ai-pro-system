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
# API CONFIG
# =========================
FD_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
FD_BASE = "https://api.football-data.org/v4"

FD_HEADERS = {
    "X-Auth-Token": FD_API_KEY
} if FD_API_KEY else {}

client = httpx.AsyncClient(timeout=15)


# =========================
# SAFE FETCH (ROBUST)
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

            # ✅ SUCCESS
            if r.status_code == 200:
                return r.json()

            # ⚠️ RATE LIMIT
            if r.status_code == 429:
                wait = 1.5 * (attempt + 1)
                logger.warning(f"Rate limited → retrying in {wait}s")
                await asyncio.sleep(wait)
                continue

            # ❌ OTHER ERRORS (log for debugging)
            logger.warning(f"API error {r.status_code} → {url}")
            return None

        except Exception as e:
            logger.error(f"Fetch exception: {e}")
            await asyncio.sleep(0.5)

    return None


# =========================
# NORMALIZE MATCH (SAFE)
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
# LIVE MATCHES (PRIMARY SOURCE)
# =========================
async def get_live_matches():

    if not FD_API_KEY:
        logger.error("Missing FOOTBALL_DATA_API_KEY")
        return {"matches": []}

    data = await fetch(
        f"{FD_BASE}/matches",
        params={"status": "LIVE"}
    )

    if not data:
        return {"matches": []}

    matches = data.get("matches", []) if isinstance(data, dict) else []

    cleaned = []
    for m in matches:
        nm = normalize_match(m)
        if nm:
            cleaned.append(nm)

    return {"matches": cleaned}


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

    cleaned = []
    for m in matches:
        nm = normalize_match(m)
        if nm:
            cleaned.append(nm)

    return {"matches": cleaned}


# =========================
# TEAM STATS (SAFE)
# =========================
async def get_team_stats(team_id: int):

    if not team_id or not FD_API_KEY:
        return {}

    data = await fetch(f"{FD_BASE}/teams/{team_id}")

    return data if isinstance(data, dict) else {}
