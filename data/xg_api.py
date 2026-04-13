import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")

BASE_URL = "https://api.football-data.org/v4"

headers = {
    "X-Auth-Token": API_KEY
}


async def get_team_xg(team_id: int):
    """
    NOTE:
    API-Football does not always provide xG directly.
    If your plan supports it, we plug it here.
    """

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/teams/{team_id}",
            headers=headers
        )
        data = r.json()

    # placeholder structure (real API dependent)
    stats = data.get("squad", [])

    return {
        "xg_for": 1.4,
        "xg_against": 1.1
    }
