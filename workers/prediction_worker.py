import asyncio
import logging

from core.queue import (
    dequeue_prediction,
    retry_prediction,
    mark_processing,
    unmark_processing
)
from core.rate_limiter import team_stats_limit, odds_api_limit
from data.odds_api import get_odds
from features.real_features import build_real_features
from models.predict import predict


# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prediction-worker")


# =========================
# PROCESS FUNCTION
# =========================
async def process(payload):

    if not isinstance(payload, dict):
        raise ValueError("Payload must be dict")

    match = payload.get("data")

    if not isinstance(match, dict):
        raise ValueError("Invalid match format")

    match_id = match.get("id")

    # -------------------------
    # RATE LIMITING
    # -------------------------
    await team_stats_limit()
    await odds_api_limit()

    # -------------------------
    # ODDS
    # -------------------------
    odds_list = await get_odds()
