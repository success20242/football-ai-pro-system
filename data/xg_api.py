import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

FOOTBALL_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")

BASE_URL = "https://api.football-data.org/v4"

headers = {
    "X-Auth-Token": FOOTBALL_API_KEY
}


# =========================
# SAFE API WRAPPER
# =========================
async def fetch(url: str):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, headers=headers)

            if r.status_code != 200:
                print(f"⚠️ API Error {r.status_code} → {url}")
                return {}

            return r.json()

    except Exception as e:
        print(f"❌ Request failed: {e}")
        return {}


# =========================
# 🧠 REAL xG (UNDERSTAT READY)
# =========================
async def get_team_xg(team_id: int):
    """
    REAL ARCHITECTURE:
    - Football-data does NOT provide xG
    - So we only return structured hook for real provider integration
    """

    data = await fetch(f"{BASE_URL}/teams/{team_id}")

    team_name = data.get("name", "UNKNOWN")

    # =========================
    # REAL xG SOURCE HOOK
    # =========================
    understat_data = await get_understat_xg(team_name)

    if understat_data and understat_data.get("xg_for") is not None:
        return {
            "xg_for": float(understat_data["xg_for"]),
            "xg_against": float(understat_data["xg_against"])
        }

    # =========================
    # HARD FAIL SAFE (NO FAKE MATH)
    # =========================
    # Instead of fake proxy → return neutral market baseline
    return {
        "xg_for": 1.35,
        "xg_against": 1.35,
        "source": "neutral_fallback"
    }


# =========================
# 🔥 REAL xG PROVIDER (UNDERSTAT SCRAPER HOOK)
# =========================
async def get_understat_xg(team_name: str):
    """
    This is where REAL xG lives.

    Options:
    - Understat scraper (recommended)
    - StatsBomb open data mapping
    - Paid xG APIs (Opta / SportMonks)

    CURRENT STATE: safe stub ONLY for structure.
    """

    # NOTE:
    # We do NOT fake xG numbers anymore.
    # This prevents model contamination.

    return {
        "xg_for": None,
        "xg_against": None,
        "status": "not_connected",
        "provider": "understat_ready"
    }
