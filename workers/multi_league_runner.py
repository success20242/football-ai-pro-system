import asyncio

from data.ingestion import fetch_matches, LEAGUES
from core.queue import enqueue_prediction


# =========================
# MULTI-LEAGUE PRODUCER
# =========================
async def run_all():

    all_count = 0

    for league in LEAGUES:

        try:
            # ⚠️ keep API call isolated per league
            data = await fetch_matches(league)

            if not isinstance(data, list):
                continue

            for match in data:
                if isinstance(match, dict):
                    await enqueue_prediction(match)
                    all_count += 1

            # 🔥 small delay = prevents API hammering
            await asyncio.sleep(0.5)

        except Exception as e:
            print(f"League error ({league}):", e)

    return {
        "status": "queued",
        "total_matches": all_count
    }


# =========================
# DEBUG RUN
# =========================
if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run_all()))
