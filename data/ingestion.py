import requests
from core.config import Config

LEAGUES = ["PL", "PD", "SA", "BL1", "CL"]

def fetch_matches(league):
    url = f"https://api.football-data.org/v4/competitions/{league}/matches"

    headers = {"X-Auth-Token": Config.FOOTBALL_API_KEY}

    res = requests.get(url, headers=headers)
    return res.json()
