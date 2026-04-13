import requests
from core.config import Config

def fetch_odds():
    url = "https://api.the-odds-api.com/v4/sports/soccer/odds"

    params = {
        "apiKey": Config.ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h"
    }

    return requests.get(url, params=params).json()
