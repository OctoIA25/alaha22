import json
import os
from datetime import datetime, timezone

import redis


def get_redis_client() -> redis.Redis:
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    return redis.Redis.from_url(redis_url, decode_responses=True)


def update_memory(task: str, step_data: dict) -> None:
    client = get_redis_client()
    payload = {
        'task': task,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'step': step_data,
    }
    client.lpush('alaha:memory:events', json.dumps(payload, ensure_ascii=False))
    client.ltrim('alaha:memory:events', 0, 199)
