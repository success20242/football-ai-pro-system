import asyncio

from data.football_api import get_live_matches, get_upcoming_matches
from core.queue import enqueue_prediction


# =========================
# PRODUCER ONLY (NO API CALLS HERE)
# =========================
async def run_live_predictions():

    matches_data = await get_live_matches()
    matches = matches_data.get("matches", []) if isinstance(matches_data, dict) else []

    if not matches:
        matches_data = await get_upcoming_matches()
        matches = matches_data.get("matches", [])

    if not matches:
        return {"status": "empty", "data": []}

    # 🔥 PUSH ALL MATCHES INTO REDIS QUEUE
    for match in matches:
        if isinstance(match, dict):
            await enqueue_prediction(match)

    return {
        "status": "queued",
        "total": len(matches),
        "message": "Matches pushed to prediction queue"
    }


# =========================
# DEBUG
# =========================
if __name__ == "__main__":
    import asyncio
    print(asyncio.run(run_live_predictions()))
