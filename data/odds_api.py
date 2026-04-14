import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ODDS_API_KEY")

BASE_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"


# =========================
# FETCH
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
# NORMALIZE (FIXED LOGIC)
# =========================
def normalize_game(game: dict):

    try:
        bookmakers = game.get("bookmakers", [])
        if not bookmakers:
            return None

        outcomes = bookmakers[0].get("markets", [{}])[0].get("outcomes", [])

        odds = {"home": None, "away": None, "draw": None}

        for o in outcomes:
            name = o.get("name", "").lower()
            price = o.get("price", 2.0)

            # FIX: proper labeling (NOT "home in name")
            if o.get("name") and "draw" in name:
                odds["draw"] = price

            elif odds["home"] is None:
                odds["home"] = price

            else:
                odds["away"] = price

        return {
            "match_id": game.get("id"),
            "home": float(odds["home"] or 2.0),
            "away": float(odds["away"] or 2.0),
            "draw": float(odds["draw"] or 3.2)
        }

    except Exception:
        return None


# =========================
# MAIN
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

    normalized = [normalize_game(g) for g in raw]

    return [g for g in normalized if g]
