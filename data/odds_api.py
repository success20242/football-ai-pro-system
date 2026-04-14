import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ODDS_API_KEY")

BASE_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"


# =========================
# SAFE FETCH
# =========================
async def fetch(params: dict):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(BASE_URL, params=params)

            if r.status_code != 200:
                return []

            data = r.json()
            return data if isinstance(data, list) else []

    except Exception:
        return []


# =========================
# ODDS NORMALIZER
# =========================
def normalize_game(game: dict):

    try:
        bookmakers = game.get("bookmakers", [])

        if not bookmakers:
            return None

        outcomes = bookmakers[0].get("markets", [{}])[0].get("outcomes", [])

        odds = {
            "home": 2.0,
            "away": 2.0,
            "draw": 3.2
        }

        for o in outcomes:
            name = o.get("name", "").lower()
            price = o.get("price", 2.0)

            if "home" in name:
                odds["home"] = price
            elif "away" in name:
                odds["away"] = price
            elif "draw" in name or "tie" in name:
                odds["draw"] = price

        return {
            "id": game.get("id") or game.get("commence_time"),
            "home": odds["home"],
            "away": odds["away"],
            "draw": odds["draw"]
        }

    except Exception:
        return None


# =========================
# MAIN ODDS FUNCTION (FIXED)
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

    raw_data = await fetch(params)

    normalized = [
        normalize_game(game)
        for game in raw_data
    ]

    return [g for g in normalized if g is not None]
