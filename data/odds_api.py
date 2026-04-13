import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ODDS_API_KEY")

BASE_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"

async def get_odds():
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    async with httpx.AsyncClient() as client:
        r = await client.get(BASE_URL, params=params)
        return r.json()
