import httpx
import logging
from core.config import Config
from core.rate_limiter import acquire_slot

logger = logging.getLogger("odds-api")
logging.basicConfig(level=logging.INFO)

client = httpx.AsyncClient(timeout=15)

ODDS_URL = "https://api.the-odds-api.com/v4/sports/soccer/odds"


# =========================
# SAFE FETCH ODDS (ASYNC)
# =========================
async def fetch_odds():

    if not Config.ODDS_API_KEY:
        logger.error("Missing ODDS_API_KEY")
        return []

    params = {
        "apiKey": Config.ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h"
    }

    try:
        await acquire_slot()

        r = await client.get(ODDS_URL, params=params)

        if r.status_code != 200:
            logger.warning(f"Odds API error {r.status_code}")
            return []

        data = r.json()

        if not isinstance(data, list):
            logger.warning("Invalid odds response format")
            return []

        return data

    except Exception as e:
        logger.error(f"Odds fetch failed: {e}")
        return []


# =========================
# CLEAN SHUTDOWN (IMPORTANT)
# =========================
async def close_client():
    await client.aclose()
