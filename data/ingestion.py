import httpx
import logging
from core.config import Config
from core.rate_limiter import acquire_slot

LEAGUES = ["PL", "PD", "SA", "BL1", "CL"]

logger = logging.getLogger("ingestion")
logging.basicConfig(level=logging.INFO)

client = httpx.AsyncClient(timeout=15)


# =========================
# SAFE ASYNC FETCH
# =========================
async def fetch(url, headers):

    try:
        await acquire_slot()

        r = await client.get(url, headers=headers)

        if r.status_code == 200:
            return r.json()

        logger.warning(f"API error {r.status_code} → {url}")
        return None

    except Exception as e:
        logger.error(f"Fetch failed: {e}")
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
            "utcDate": m.get("utcDate"),
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

    except Exception:
        return None


# =========================
# FETCH MATCHES (FIXED)
# =========================
async def fetch_matches(league):

    if not Config.FOOTBALL_API_KEY:
        logger.error("Missing FOOTBALL_API_KEY")
        return []

    url = f"https://api.football-data.org/v4/competitions/{league}/matches"

    headers = {
        "X-Auth-Token": Config.FOOTBALL_API_KEY
    }

    data = await fetch(url, headers)

    if not data or not isinstance(data, dict):
        return []

    matches = data.get("matches", [])

    cleaned = []
    for m in matches:
        nm = normalize_match(m)
        if nm:
            cleaned.append(nm)

    return cleaned


# =========================
# CLEAN SHUTDOWN (IMPORTANT)
# =========================
async def close_client():
    await client.aclose()
