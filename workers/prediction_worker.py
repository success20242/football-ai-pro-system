import asyncio

from core.queue import dequeue_prediction
from core.rate_limiter import acquire_slot
from data.football_api import get_team_stats
from features.real_features import build_real_features
from models.predict import predict


async def process(match):
    features = await build_real_features(match, {})
    prediction = predict(features)

    return {
        "match_id": match.get("id"),
        "prediction": prediction
    }


async def worker():
    print("🚀 Prediction worker running...")

    while True:
        job = await dequeue_prediction()

        if not job:
            await asyncio.sleep(0.2)
            continue

        allowed = await acquire_slot()

        if not allowed:
            # requeue job if rate limited
            from core.queue import enqueue_prediction
            await enqueue_prediction(job)
            await asyncio.sleep(0.3)
            continue

        try:
            await process(job)

        except Exception as e:
            print("Worker error:", e)
