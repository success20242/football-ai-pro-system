import os
from dotenv import load_dotenv

load_dotenv()


# =========================
# CORE CONFIG CLASS
# =========================
class Config:

    # -------------------------
    # API KEYS (VALIDATED)
    # -------------------------
    FOOTBALL_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
    ODDS_API_KEY = os.getenv("ODDS_API_KEY")

    # -------------------------
    # DATABASE
    # -------------------------
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_NAME = os.getenv("POSTGRES_DB", "betting")
    DB_USER = os.getenv("POSTGRES_USER", "postgres")
    DB_PASS = os.getenv("POSTGRES_PASSWORD", "")

    # -------------------------
    # MODEL / BETTING RULES
    # -------------------------
    VALUE_THRESHOLD = float(os.getenv("VALUE_BET_THRESHOLD", 0.05))
    LIVE_INTERVAL = int(os.getenv("LIVE_POLL_INTERVAL", 30))

    MAX_KELLY_FRACTION = float(os.getenv("MAX_KELLY_FRACTION", 0.25))
    MAX_BET_PERCENT = float(os.getenv("MAX_BET_PERCENT", 0.05))

    # -------------------------
    # SYSTEM FLAGS (IMPORTANT UPGRADE)
    # -------------------------
    USE_LIVE_BETS = os.getenv("USE_LIVE_BETS", "true").lower() == "true"
    USE_ODDS_API = os.getenv("USE_ODDS_API", "true").lower() == "true"
    USE_XG_API = os.getenv("USE_XG_API", "false").lower() == "true"

    # -------------------------
    # INTERNAL SAFETY CHECK
    # -------------------------
    @classmethod
    def validate(cls):
        missing = []

        if not cls.FOOTBALL_API_KEY:
            missing.append("FOOTBALL_DATA_API_KEY")

        if not cls.ODDS_API_KEY:
            missing.append("ODDS_API_KEY")

        if missing:
            raise ValueError(f"Missing required config: {missing}")


# =========================
# AUTO VALIDATION ON IMPORT
# =========================
try:
    Config.validate()
except Exception as e:
    import logging
    logging.warning(f"⚠️ Config validation warning: {e}")
