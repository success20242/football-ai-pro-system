import asyncio
import logging

from data.ingestion import fetch_matches, LEAGUES
from core.queue import enqueue_prediction
from core.rate_limiter import acquire_slot


# =========================
# LOGGING
# =========================
logger = logging.getLogger("multi-league-runner")
logging.basicConfig(level=logging.INFO)


# =========================
# CONFIG
# =========================
MAX_CONCURRENT_LEAGUES = 3
QUEUE_DELAY = 0.05


# =========================
# PROCESS SINGLE LEAGUE
# =========================
async def process_league(league: str):

    if not league:
        return 0

    count = 0

    try:
        allowed = await acquire_slot()
        if not allowed:
            await asyncio.sleep(0.5)

        data = await fetch_matches(league)

        if not isinstance(data, list):
            logger.warning(f"{league}: invalid data type {type(data)}")
            return 0

        for match in data:
            if not isinstance(match, dict):
                continue

            # 🔒 ensure ID exists (prevents worker crashes later)
            if not match.get("id"):
                continue

            await enqueue_prediction(match)
            count += 1

            await asyncio.sleep(QUEUE_DELAY)

        logger.info(f"📊 {league}: queued {count} matches")

    except Exception as e:
        logger.error(f"❌ {league} error: {e}")

    return count


# =========================
# MULTI-LEAGUE PRODUCER
# =========================
async def run_all():

    if not LEAGUES:
        logger.error("No leagues configured")
        return {"status": "error", "message": "No leagues"}

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_LEAGUES)

    async def safe_process(league):
        async with semaphore:
            return await process_league(league)

    tasks = [safe_process(l) for l in LEAGUES]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    total = 0
    for r in results:
        if isinstance(r, int):
            total += r

    return {
        "status": "queued",
        "total_matches": total,
        "leagues": len(LEAGUES)
    }


# =========================
# DEBUG
# =========================
if __name__ == "__main__":
    print(asyncio.run(run_all()))
