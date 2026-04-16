import os
import asyncio
import logging
import random
import httpx
from dotenv import load_dotenv

from core.rate_limiter import acquire_slot

load_dotenv()

logger = logging.getLogger("odds-api")
logging.basicConfig(level=logging.INFO)

API_KEY = os.getenv("ODDS_API_KEY")

BASE_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"

client = httpx.AsyncClient(timeout=10)


# =========================
# SAFE FETCH (FIXED)
# =========================
async def fetch(params: dict, retries=2):

    for attempt in range(retries + 1):

        try:
            await acquire_slot()

            r = await client.get(BASE_URL, params=params)

            if r.status_code == 200:
                data = r.json()
                return data if isinstance(data, list) else []

            if r.status_code == 429:
                wait = (1.5 * (attempt + 1)) + random.uniform(0.2, 1.0)
                logger.warning(f"⚠️ ODDS 429 retry {attempt+1} in {wait:.2f}s")
                await asyncio.sleep(wait)
                continue

            logger.warning(f"❌ ODDS ERROR {r.status_code}")
            return []

        except Exception as e:
            logger.error(f"❌ FETCH ERROR → {e}")
            await asyncio.sleep(0.5 + random.random())

    return []


# =========================
# IMPLIED PROBABILITY
# =========================
def implied_prob(odds: float):
    try:
        return 1.0 / float(odds) if odds and odds > 1 else 0.0
    except:
        return 0.0


# =========================
# SAFE NORMALIZER (FIXED CORE BUG)
# =========================
def normalize_game(game: dict):

    try:
        if not isinstance(game, dict):
            return None

        bookmakers = game.get("bookmakers", [])
        if not bookmakers:
            return None

        outcomes = None

        for bm in bookmakers:
            for market in bm.get("markets", []):
                if market.get("key") == "h2h":
                    outcomes = market.get("outcomes", [])
                    break
            if outcomes:
                break

        if not outcomes:
            return None

        # -------------------------
        # DETECT TEAM NAMES FROM OUTCOMES ONLY
        # (FIX: removes dependency on broken fields)
        # -------------------------
        home = outcomes[0]
        away = outcomes[1] if len(outcomes) > 1 else None

        if not home or not away:
            return None

        home_name = home.get("name", "").lower().strip()
        away_name = away.get("name", "").lower().strip()

        odds = {
            "home": float(home.get("price", 2.0)),
            "away": float(away.get("price", 2.0)),
            "draw": None
        }

        for o in outcomes:
            if "draw" in o.get("name", "").lower():
                odds["draw"] = float(o.get("price", 3.2))

        draw = odds["draw"] or 3.2

        # -------------------------
        # PROBABILITIES
        # -------------------------
        h = implied_prob(odds["home"])
        d = implied_prob(draw)
        a = implied_prob(odds["away"])

        total = h + d + a
        if total > 0:
            h, d, a = h / total, d / total, a / total

        match_key = f"{home_name}_{away_name}"

        return {
            "match_key": match_key,
            "home": odds["home"],
            "draw": draw,
            "away": odds["away"],
            "probs": {
                "home": round(h, 4),
                "draw": round(d, 4),
                "away": round(a, 4)
            }
        }

    except Exception as e:
        logger.error(f"❌ NORMALIZE ERROR → {e}")
        return None


# =========================
# MAIN ENTRY
# =========================
async def get_odds():

    if not API_KEY:
        logger.warning("⚠️ NO ODDS API KEY")
        return []

    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    raw = await fetch(params)

    return [g for g in (normalize_game(x) for x in raw) if g]
