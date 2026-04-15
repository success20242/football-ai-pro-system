import json
from core.redis_client import redis_client

QUEUE_KEY = "football:prediction_queue"


async def enqueue_prediction(match: dict):
    await redis_client.rpush(QUEUE_KEY, json.dumps(match))


async def dequeue_prediction():
    data = await redis_client.lpop(QUEUE_KEY)
    return json.loads(data) if data else None
