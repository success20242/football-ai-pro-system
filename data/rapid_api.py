import os
import logging
import httpx

from core.rate_limiter import acquire_slot

logger = logging.getLogger("rapid-api")
logging.basicConfig(level=logging.INFO)

API_KEY = os.getenv("FOOTBALL_API_KEY")

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

# =========================
# GLOBAL CLIENT (FIXED)
# =========================
client = httpx.AsyncClient(timeout=15)


# =========================
# SAFE FETCH (IMPROVED)
# =========================
async def fetch(endpoint, params=None):

    if not API_KEY:
        logger.error("Missing FOOTBALL_API_KEY")
        return {}

    try:
        await acquire_slot()

        r = await client.get(
            f"{BASE_URL}/{endpoint}",
            headers={
                "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
                "x-rapidapi-key": API_KEY
            },
            params=params or {}
        )

        if r.status_code != 200:
            logger.warning(f"RapidAPI error {r.status_code}")
            return {}

        data = r.json()

        # -------------------------
        # VALIDATION GUARD
        # -------------------------
        if not isinstance(data, dict):
            return {}

        if "errors" in data and data["errors"]:
            logger.warning(f"RapidAPI returned errors: {data['errors']}")
            return {}

        return data

    except Exception as e:
        logger.error(f"RapidAPI fetch error: {e}")
        return {}


# =========================
# CLEAN SHUTDOWN (IMPORTANT)
# =========================
async def close_client():
    await client.aclose()
