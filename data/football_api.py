import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")

BASE_URL = "https://api.football-data.org/v4"

headers = {
    "X-Auth-Token": API_KEY
}


# =========================
# SAFE HTTP CLIENT WRAPPER
# =========================
async def fetch(url: str):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, headers=headers)

            if r.status_code != 200:
                print(f"⚠️ API Error {r.status_code}: {url}")
                return {}

            return r.json()

    except Exception as e:
        print(f"❌ Request failed: {e}")
        return {}


# =========================
# LIVE MATCHES
# =========================
async def get_live_matches():
    url = f"{BASE_URL}/matches?status=LIVE"
    return await fetch(url)


# =========================
# TEAM STATS
# =========================
async def get_team_stats(team_id: int):
    url = f"{BASE_URL}/teams/{team_id}"
    return await fetch(url)


# =========================
# FIXTURES / COMPETITION MATCHES
# =========================
async def get_fixtures(competition="PL"):
    url = f"{BASE_URL}/competitions/{competition}/matches"
    return await fetch(url)
