import json
import uuid
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as aioredis

from app.config import settings

_redis: Optional[aioredis.Redis] = None


async def init_redis() -> None:
    global _redis
    _redis = aioredis.from_url(settings.redis_url, decode_responses=True)


async def close_redis() -> None:
    if _redis:
        await _redis.aclose()


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis가 초기화되지 않았습니다")
    return _redis


async def create_session(data: dict) -> tuple[str, dict]:
    session_id = str(uuid.uuid4())
    payload = {
        "session_id": session_id,
        "status": "ready",
        "parsed": data,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await get_redis().setex(
        f"session:{session_id}",
        settings.session_ttl,
        json.dumps(payload, ensure_ascii=False),
    )
    return session_id, payload


async def get_session(session_id: str) -> Optional[dict]:
    raw = await get_redis().get(f"session:{session_id}")
    if raw is None:
        return None
    return json.loads(raw)


async def delete_session(session_id: str) -> bool:
    deleted = await get_redis().delete(f"session:{session_id}")
    return deleted > 0


async def update_session(session_id: str, data: dict) -> None:
    await get_redis().setex(
        f"session:{session_id}",
        settings.session_ttl,
        json.dumps(data, ensure_ascii=False),
    )
