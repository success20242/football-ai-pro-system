import os
import httpx
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY")


BASE_URL = "https://api.the-odds-api.com/v4"


async def get_odds():
    """
    Fetch soccer odds data
    """

    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                f"{BASE_URL}/sports/soccer_epl/odds",
                params={
                    "apiKey": ODDS_API_KEY,
                    "regions": "eu",
                    "markets": "h2h"
                }
            )

            return r.json()

        except Exception as e:
            print("Odds API error:", e)
            return []
