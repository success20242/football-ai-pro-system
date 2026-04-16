import asyncio
import logging
import time

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
MAX_RETRIES = 3


# =========================
# SAFE RATE LIMIT ACQUISITION
# =========================
async def wait_for_slot():

    for _ in range(10):  # retry window
        allowed = await acquire_slot()

        if allowed:
            return True

        await asyncio.sleep(0.2)

    return False


# =========================
# PROCESS SINGLE LEAGUE (UPGRADED)
# =========================
async def process_league(league: str):

    if not league:
        return 0

    start_time = time.time()
    count = 0

    try:
        # -------------------------
        # RATE LIMIT CONTROL (FIXED)
        # -------------------------
        allowed = await wait_for_slot()

        if not allowed:
            logger.warning(f"⚠️ Rate limit blocked league: {league}")
            return 0

        # -------------------------
        # FETCH MATCHES
        # -------------------------
        data = await fetch_matches(league)

        if not isinstance(data, list):
            logger.warning(f"⚠️ {league}: invalid data type {type(data)}")
            return 0

        # -------------------------
        # PROCESS MATCHES
        # -------------------------
        for match in data:

            if not isinstance(match, dict):
                continue

            match_id = match.get("id")
            if not match_id:
                continue

            # retry-safe enqueue
            success = False

            for attempt in range(MAX_RETRIES):
                try:
                    await enqueue_prediction(match)
                    success = True
                    break
                except Exception as e:
                    logger.warning(
                        f"⚠️ enqueue failed (attempt {attempt+1}) "
                        f"league={league} match={match_id} err={e}"
                    )
                    await asyncio.sleep(0.1)

            if success:
                count += 1

            await asyncio.sleep(QUEUE_DELAY)

        duration = time.time() - start_time

        logger.info(
            f"📊 {league}: queued={count} duration={duration:.2f}s"
        )

    except Exception as e:
        logger.error(f"❌ {league} fatal error: {e}")

    return count


# =========================
# MULTI-LEAGUE RUNNER (IMPROVED)
# =========================
async def run_all():

    if not LEAGUES:
        logger.error("No leagues configured")
        return {"status": "error", "message": "No leagues"}

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_LEAGUES)

    async def safe_process(league):
        async with semaphore:
            return await process_league(league)

    start_time = time.time()

    tasks = [safe_process(l) for l in LEAGUES]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    total = 0
    failed = 0

    for r in results:
        if isinstance(r, int):
            total += r
        else:
            failed += 1

    duration = time.time() - start_time

    return {
        "status": "queued",
        "total_matches": total,
        "leagues": len(LEAGUES),
        "failed_leagues": failed,
        "duration_sec": round(duration, 2)
    }


# =========================
# DEBUG RUN
# =========================
if __name__ == "__main__":
    print(asyncio.run(run_all()))
