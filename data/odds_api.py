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

client = httpx.AsyncClient(timeout=10)


# =========================
# SAFE FETCH
# =========================
async def fetch(params: dict, retries=2):

    for attempt in range(retries + 1):
        try:
            if not await acquire_slot():
                await asyncio.sleep(0.3)

            r = await client.get(BASE_URL, params=params)

            if r.status_code == 200:
                data = r.json()
                return data if isinstance(data, list) else []

            if r.status_code == 429:
                logger.warning(f"⚠️ ODDS 429 retry {attempt+1}")
                await asyncio.sleep(1.5 * (attempt + 1))
                continue

            logger.warning(f"❌ ODDS ERROR {r.status_code}")
            return []

        except Exception as e:
            logger.error(f"❌ FETCH ERROR → {e}")
            await asyncio.sleep(0.5)

    return []


# =========================
# TEAM NORMALIZER (SYNC WITH FEATURES)
# =========================
def normalize_team(name: str):
    if not name:
        return ""

    name = name.lower().strip()

    replacements = {
        "fc": "",
        "cf": "",
        "afc": "",
        "club": ""
    }

    for k, v in replacements.items():
        name = name.replace(k, v)

    return " ".join(name.split())


# =========================
# IMPLIED PROBABILITY
# =========================
def implied_prob(odds: float):
    try:
        return 1.0 / float(odds) if odds else 0.0
    except:
        return 0.0


# =========================
# NORMALIZE GAME (KEY FIXED)
# =========================
def normalize_game(game: dict):

    try:
        raw_home = game.get("home_team")
        raw_away = game.get("away_team")

        home_team = normalize_team(raw_home)
        away_team = normalize_team(raw_away)

        if not home_team or not away_team:
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

        odds = {"home": None, "away": None, "draw": None}

        # -------------------------
        # MATCH BY TEAM NAME
        # -------------------------
        for o in outcomes:
            name = normalize_team(o.get("name"))
            price = float(o.get("price") or 2.0)

            if "draw" in name:
                odds["draw"] = price
            elif name == home_team:
                odds["home"] = price
            elif name == away_team:
                odds["away"] = price

        # -------------------------
        # FALLBACK
        # -------------------------
        fallback_prices = [float(o.get("price") or 2.0) for o in outcomes]

        if odds["home"] is None and len(fallback_prices) > 0:
            odds["home"] = fallback_prices[0]

        if odds["away"] is None and len(fallback_prices) > 1:
            odds["away"] = fallback_prices[1]

        if odds["home"] is None or odds["away"] is None:
            return None

        draw = odds["draw"] if odds["draw"] else 3.2

        # -------------------------
        # IMPLIED PROBS
        # -------------------------
        home_p = implied_prob(odds["home"])
        draw_p = implied_prob(draw)
        away_p = implied_prob(odds["away"])

        total = home_p + draw_p + away_p
        if total > 0:
            home_p /= total
            draw_p /= total
            away_p /= total

        # =========================
        # 🔥 CRITICAL FIX: MATCH KEY
        # =========================
        match_key = f"{home_team}_{away_team}"

        return {
            "match_key": match_key,

            "home": float(odds["home"]),
            "draw": float(draw),
            "away": float(odds["away"]),

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
# MAIN
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

    normalized = []

    for game in raw:
        parsed = normalize_game(game)
        if parsed:
            normalized.append(parsed)

    logger.info(f"✅ ODDS LOADED: {len(normalized)} matches")

    return normalized
