import httpx
import os
import hashlib
import logging

from core.rate_limiter import acquire_slot

logger = logging.getLogger("xg-api")
logging.basicConfig(level=logging.INFO)

FOOTBALL_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
BASE_URL = "https://api.football-data.org/v4"

HEADERS = {
    "X-Auth-Token": FOOTBALL_API_KEY
} if FOOTBALL_API_KEY else {}

# =========================
# GLOBAL CLIENT (FIXED)
# =========================
client = httpx.AsyncClient(timeout=15)


# =========================
# SAFE API WRAPPER (FIXED)
# =========================
async def fetch(url: str):

    try:
        await acquire_slot()

        r = await client.get(url, headers=HEADERS)

        if r.status_code != 200:
            logger.warning(f"xG API error {r.status_code}")
            return None

        data = r.json()

        if not isinstance(data, dict):
            return None

        return data

    except Exception as e:
        logger.error(f"xG fetch error: {e}")
        return None


# =========================
# DETERMINISTIC xG BASELINE (STABLE)
# =========================
def pseudo_xg_from_team(team_name: str):

    seed = int(hashlib.md5(team_name.encode()).hexdigest(), 16)

    # bounded & normalized for stability
    xg_for = 1.2 + ((seed % 100) / 120.0)       # ~1.2 - 2.0
    xg_against = 0.9 + ((seed % 80) / 140.0)    # ~0.9 - 1.5

    return {
        "xg_for": round(xg_for, 3),
        "xg_against": round(xg_against, 3),
        "source": "deterministic_proxy"
    }


# =========================
# SAFE TEAM NAME RESOLVER
# =========================
def safe_team_name(data, team_id: int):

    if isinstance(data, dict):
        return data.get("name") or f"team_{team_id}"

    return f"team_{team_id}"


# =========================
# UNDERSTAT HOOK (STABLE PLACEHOLDER)
# =========================
async def get_understat_xg(team_name: str):

    # explicitly safe placeholder
    return None


# =========================
# MAIN xG PIPELINE
# =========================
async def get_team_xg(team_id: int):

    data = await fetch(f"{BASE_URL}/teams/{team_id}")

    if not data:
        logger.info(f"xG fallback used for team {team_id}")
        return pseudo_xg_from_team(f"team_{team_id}")

    team_name = safe_team_name(data, team_id)

    understat_data = await get_understat_xg(team_name)

    if isinstance(understat_data, dict):
        return {
            "xg_for": float(understat_data.get("xg_for", 0.0)),
            "xg_against": float(understat_data.get("xg_against", 0.0)),
            "source": "understat"
        }

    return pseudo_xg_from_team(team_name)


# =========================
# CLEAN SHUTDOWN (IMPORTANT)
# =========================
async def close_client():
    await client.aclose()
