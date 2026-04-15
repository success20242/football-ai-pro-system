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
MAX_CONCURRENT_LEAGUES = 3   # prevents API overload
QUEUE_DELAY = 0.05          # smooth queue flow


# =========================
# PROCESS SINGLE LEAGUE
# =========================
async def process_league(league: str):

    count = 0

    try:
        # 🔒 Rate limit per league fetch
        allowed = await acquire_slot()
        if not allowed:
            await asyncio.sleep(0.5)

        data = await fetch_matches(league)

        if not isinstance(data, list):
            logger.warning(f"{league}: invalid data")
            return 0

        for match in data:
            if not isinstance(match, dict):
                continue

            await enqueue_prediction(match)
            count += 1

            # 🔥 smooth queue (prevents Redis spike)
            await asyncio.sleep(QUEUE_DELAY)

        logger.info(f"{league}: queued {count} matches")

    except Exception as e:
        logger.error(f"{league} error: {e}")

    return count


# =========================
# MULTI-LEAGUE PRODUCER
# =========================
async def run_all():

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_LEAGUES)

    async def safe_process(league):
        async with semaphore:
            return await process_league(league)

    tasks = [safe_process(league) for league in LEAGUES]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    total = sum(r for r in results if isinstance(r, int))

    return {
        "status": "queued",
        "total_matches": total,
        "leagues": len(LEAGUES)
    }


# =========================
# DEBUG RUN
# =========================
if __name__ == "__main__":
    print(asyncio.run(run_all()))
