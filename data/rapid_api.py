# data/rapid_api.py

import os
import httpx

API_KEY = os.getenv("FOOTBALL_API_KEY")

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"


async def fetch(endpoint, params=None):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{BASE_URL}/{endpoint}",
                headers={
                    "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
                    "x-rapidapi-key": API_KEY
                },
                params=params or {}
            )

            if r.status_code != 200:
                return {}

            return r.json()

    except Exception:
        return {}
