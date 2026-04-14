import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ODDS_API_KEY")

BASE_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"


# =========================
# SAFE HTTP WRAPPER
# =========================
async def fetch(params: dict):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(BASE_URL, params=params)

            if r.status_code != 200:
                print(f"⚠️ Odds API error {r.status_code}")
                return []

            return r.json()

    except Exception as e:
        print(f"❌ Odds request failed: {e}")
        return []


# =========================
# MAIN ODDS FUNCTION (FIXED CONTRACT)
# =========================
async def get_odds():
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    return await fetch(params)
