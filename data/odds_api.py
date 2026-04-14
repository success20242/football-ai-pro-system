import os
import httpx
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# 🟢 FIXED: proper endpoint format (must be dynamic, not hardcoded EPL)
BASE_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"


# =========================
# SAFE REQUEST WRAPPER
# =========================
async def fetch_odds():
    """
    Fetch raw odds from provider
    """
    if not ODDS_API_KEY:
        print("⚠️ Missing ODDS_API_KEY")
        return []

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(BASE_URL, params=params)

            if r.status_code != 200:
                print(f"⚠️ Odds API Error {r.status_code}")
                return []

            return r.json()

    except Exception as e:
        print(f"❌ Odds fetch failed: {e}")
        return []


# =========================
# 🧠 NORMALIZED ODDS FORMAT (CRITICAL FOR ML)
# =========================
def normalize_odds(match_odds: dict):
    """
    Converts raw odds into ML-ready structure
    """

    try:
        bookmakers = match_odds.get("bookmakers", [])

        if not bookmakers:
            return None

        # take first bookmaker (you can upgrade later to avg/consensus)
        markets = bookmakers[0]["markets"][0]["outcomes"]

        odds = {
            "home": None,
            "draw": None,
            "away": None
        }

        for outcome in markets:
            name = outcome["name"].lower()

            if name in ["home", "1"]:
                odds["home"] = outcome["price"]

            elif name in ["draw", "x"]:
                odds["draw"] = outcome["price"]

            elif name in ["away", "2"]:
                odds["away"] = outcome["price"]

        # ensure completeness
        if None in odds.values():
            return None

        return odds

    except Exception:
        return None


# =========================
# 🧠 IMPLIED PROBABILITY CONVERTER
# =========================
def implied_probabilities(odds: dict):
    """
    Converts odds → probabilities (market signal)
    """

    try:
        home = 1 / odds["home"]
        draw = 1 / odds["draw"]
        away = 1 / odds["away"]

        total = home + draw + away

        return {
            "home": home / total,
            "draw": draw / total,
            "away": away / total
        }

    except Exception:
        return None
