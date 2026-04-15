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
RAPID_API_KEY = os.getenv("FOOTBALL_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

FD_BASE = "https://api.football-data.org/v4"
RAPID_BASE = "https://api-football-v1.p.rapidapi.com/v3"
ODDS_BASE = "https://api.the-odds-api.com/v4"


# =========================
# HEADERS
# =========================
FD_HEADERS = {"X-Auth-Token": FD_API_KEY} if FD_API_KEY else {}

RAPID_HEADERS = {
    "x-rapidapi-key": RAPID_API_KEY,
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
} if RAPID_API_KEY else {}


# =========================
# SHARED HTTP CLIENT (PERF BOOST)
# =========================
client = httpx.AsyncClient(timeout=10)


# =========================
# SMART FETCH (RETRY + RATE LIMIT)
# =========================
async def fetch(url: str, headers=None, params=None, retries=2):

    for attempt in range(retries + 1):

        try:
            # 🔒 global rate limiter
            allowed = await acquire_slot()
            if not allowed:
                await asyncio.sleep(0.3)

            r = await client.get(url, headers=headers, params=params)

            if r.status_code == 200:
                return r.json()

            if r.status_code == 429:
                logger.warning(f"⚠️ 429 Rate limit → retry {attempt+1}")
                await asyncio.sleep(1.5 * (attempt + 1))
                continue

            logger.warning(f"❌ API {r.status_code} → {url}")
            return None

        except Exception as e:
            logger.error(f"❌ Fetch error: {e}")
            await asyncio.sleep(0.5)

    return None


# =========================
# SAFE HELPERS
# =========================
def safe_dict(data):
    return data if isinstance(data, dict) else {}


def safe_list(data):
    return data if isinstance(data, list) else []


# =========================
# NORMALIZERS
# =========================
def normalize_fd_match(m):
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
    except Exception:
        return None


def normalize_rapid_match(m):
    try:
        return {
            "id": m.get("fixture", {}).get("id"),
            "league": m.get("league", {}).get("name"),
            "timestamp": m.get("fixture", {}).get("date"),
            "status": m.get("fixture", {}).get("status", {}).get("short"),
            "homeTeam": {
                "id": m.get("teams", {}).get("home", {}).get("id"),
                "name": m.get("teams", {}).get("home", {}).get("name")
            },
            "awayTeam": {
                "id": m.get("teams", {}).get("away", {}).get("id"),
                "name": m.get("teams", {}).get("away", {}).get("name")
            }
        }
    except Exception:
        return None


# =========================
# LIVE MATCHES
# =========================
async def get_live_matches():

    # ✅ RAPID FIRST
    if RAPID_API_KEY:
        data = await fetch(
            f"{RAPID_BASE}/fixtures",
            headers=RAPID_HEADERS,
            params={"live": "all"}
        )

        matches = safe_list(data.get("response") if data else [])
        cleaned = [normalize_rapid_match(m) for m in matches]
        cleaned = [m for m in cleaned if m]

        if cleaned:
            return {"matches": cleaned}

    # ⚠️ FALLBACK
    if FD_API_KEY:
        data = await fetch(
            f"{FD_BASE}/matches",
            headers=FD_HEADERS,
            params={"status": "LIVE"}
        )

        matches = safe_list(data.get("matches") if data else [])
        cleaned = [normalize_fd_match(m) for m in matches]

        return {"matches": [m for m in cleaned if m]}

    return {"matches": []}


# =========================
# UPCOMING MATCHES
# =========================
async def get_upcoming_matches():

    if RAPID_API_KEY:
        data = await fetch(
            f"{RAPID_BASE}/fixtures",
            headers=RAPID_HEADERS,
            params={"next": 10}
        )

        matches = safe_list(data.get("response") if data else [])
        return {"matches": [normalize_rapid_match(m) for m in matches if m]}

    if FD_API_KEY:
        data = await fetch(f"{FD_BASE}/matches", headers=FD_HEADERS)

        matches = safe_list(data.get("matches") if data else [])
        return {"matches": [normalize_fd_match(m) for m in matches if m]}

    return {"matches": []}


# =========================
# TEAM STATS
# =========================
async def get_team_stats(team_id: int):

    if not team_id:
        return {}

    # ✅ RAPID FIRST
    if RAPID_API_KEY:
        data = await fetch(
            f"{RAPID_BASE}/teams",
            headers=RAPID_HEADERS,
            params={"id": team_id}
        )

        response = safe_list(data.get("response") if data else [])
        if response:
            return response[0]

    # ⚠️ FALLBACK
    if FD_API_KEY:
        data = await fetch(
            f"{FD_BASE}/teams/{team_id}",
            headers=FD_HEADERS
        )
        return safe_dict(data)

    return {}
