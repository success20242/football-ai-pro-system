import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ODDS_API_KEY")

BASE_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"


# =========================
# FETCH (SAFE JSON HANDLING)
# =========================
async def fetch(params: dict):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(BASE_URL, params=params)

            if r.status_code != 200:
                return []

            data = r.json()

            # FIX: ensure list output only if valid
            if isinstance(data, list):
                return data

            return data.get("data", []) if isinstance(data, dict) else []

    except Exception:
        return []


# =========================
# NORMALIZE GAME (FIXED MARKET PARSING)
# =========================
def normalize_game(game: dict):
    try:
        if not isinstance(game, dict):
            return None

        bookmakers = game.get("bookmakers", [])
        if not bookmakers or not isinstance(bookmakers, list):
            return None

        markets = bookmakers[0].get("markets", [])
        if not markets:
            return None

        outcomes = markets[0].get("outcomes", [])
        if not outcomes:
            return None

        odds = {"home": None, "away": None, "draw": None}

        for o in outcomes:
            if not isinstance(o, dict):
                continue

            name = (o.get("name") or "").lower()
            price = o.get("price") or 2.0

            # FIXED CLASSIFICATION LOGIC
            if "draw" in name:
                odds["draw"] = float(price)

            elif odds["home"] is None:
                odds["home"] = float(price)

            else:
                odds["away"] = float(price)

        if odds["home"] is None or odds["away"] is None:
            return None

        return {
            "match_id": game.get("id"),
            "home": odds["home"],
            "away": odds["away"],
            "draw": odds["draw"] if odds["draw"] is not None else 3.2
        }

    except Exception:
        return None


# =========================
# MAIN ODDS PIPELINE
# =========================
async def get_odds():

    if not API_KEY:
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

    for g in raw:
        parsed = normalize_game(g)
        if parsed:
            normalized.append(parsed)

    return normalized
