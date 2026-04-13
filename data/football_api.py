import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")

BASE_URL = "https://api.football-data.org/v4"

headers = {
    "X-Auth-Token": API_KEY
}

async def get_live_matches():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/matches", headers=headers)
        return r.json()

async def get_team_stats(team_id):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/teams/{team_id}", headers=headers)
        return r.json()

async def get_fixtures(competition="PL"):
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/competitions/{competition}/matches",
            headers=headers
        )
        return r.json()
