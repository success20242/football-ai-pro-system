import os
import asyncio
import logging
import httpx
from dotenv import load_dotenv

from core.rate_limiter import acquire_slot

load_dotenv()

logger = logging.getLogger("odds-api")
logging.basicConfig(level=logging.INFO)

API_KEY = os.getenv("ODDS_API_KEY")

BASE_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"

# =========================
# SHARED CLIENT (PERFORMANCE)
# =========================
client = httpx.AsyncClient(timeout=10)


# =========================
# SAFE FETCH (RETRY + RATE LIMIT)
# =========================
async def fetch(params: dict, retries=2):

    for attempt in range(retries + 1):

        try:
            # 🔒 global limiter
            allowed = await acquire_slot()
            if not allowed:
                await asyncio.sleep(0.3)

            r = await client.get(BASE_URL, params=params)

            if r.status_code == 200:
                data = r.json()
                return data if isinstance(data, list) else []

            if r.status_code == 429:
                logger.warning(f"⚠️ ODDS 429 → retry {attempt+1}")
                await asyncio.sleep(1.5 * (attempt + 1))
                continue

            logger.warning(f"❌ ODDS API ERROR {r.status_code}")
            return []

        except Exception as e:
            logger.error(f"❌ ODDS FETCH ERROR → {e}")
            await asyncio.sleep(0.5)

    return []


# =========================
# IMPLIED PROBABILITY
# =========================
def implied_prob(odds: float):
    try:
        return 1.0 / float(odds) if odds else 0.0
    except Exception:
        return 0.0


# =========================
# NORMALIZE GAME (ROBUST)
# =========================
def normalize_game(game: dict):

    try:
        if not isinstance(game, dict):
            return None

        game_id = game.get("id")
        home_team = (game.get("home_team") or "").lower()
        away_team = (game.get("away_team") or "").lower()

        bookmakers = game.get("bookmakers", [])
        if not bookmakers:
            return None

        # ✅ find first valid market
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

        odds = {"home": None, "away": None, "draw": None}

        # -------------------------
        # MATCH BY NAME FIRST
        # -------------------------
        for o in outcomes:
            name = (o.get("name") or "").lower()
            price = float(o.get("price") or 2.0)

            if "draw" in name:
                odds["draw"] = price
            elif home_team and name == home_team:
                odds["home"] = price
            elif away_team and name == away_team:
                odds["away"] = price

        # -------------------------
        # FALLBACK ORDER MATCH
        # -------------------------
        for o in outcomes:
            price = float(o.get("price") or 2.0)

            if odds["home"] is None:
                odds["home"] = price
            elif odds["away"] is None:
                odds["away"] = price

        if odds["home"] is None or odds["away"] is None:
            return None

        draw = odds["draw"] if odds["draw"] else 3.2

        # -------------------------
        # IMPLIED PROBABILITIES
        # -------------------------
        home_p = implied_prob(odds["home"])
        draw_p = implied_prob(draw)
        away_p = implied_prob(odds["away"])

        # normalize probabilities (remove bookmaker margin)
        total = home_p + draw_p + away_p
        if total > 0:
            home_p /= total
            draw_p /= total
            away_p /= total

        return {
            "match_id": game_id,   # 🔥 unified key (IMPORTANT)
            "home": float(odds["home"]),
            "draw": float(draw),
            "away": float(odds["away"]),

            # 🔥 clean model-ready probabilities
            "probs": {
                "home": round(home_p, 4),
                "draw": round(draw_p, 4),
                "away": round(away_p, 4)
            }
        }

    except Exception as e:
        logger.error(f"❌ NORMALIZE ERROR → {e}")
        return None


# =========================
# MAIN PIPELINE
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

    if not isinstance(raw, list):
        return []

    normalized = []

    for game in raw:
        parsed = normalize_game(game)
        if parsed:
            normalized.append(parsed)

    logger.info(f"✅ ODDS LOADED: {len(normalized)} matches")

    return normalized
