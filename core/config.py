import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    FOOTBALL_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
    ODDS_API_KEY = os.getenv("ODDS_API_KEY")

    DB_HOST = os.getenv("POSTGRES_HOST")
    DB_NAME = os.getenv("POSTGRES_DB")
    DB_USER = os.getenv("POSTGRES_USER")
    DB_PASS = os.getenv("POSTGRES_PASSWORD")

    VALUE_THRESHOLD = float(os.getenv("VALUE_BET_THRESHOLD", 0.05))
    LIVE_INTERVAL = int(os.getenv("LIVE_POLL_INTERVAL", 30))
