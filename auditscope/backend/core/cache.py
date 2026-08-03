"""缓存层 seam：get/set。

有 Redis 走 Redis；否则内存兜底（演示/单进程）。调用方不关心后端。
"""
from __future__ import annotations
import json
import time
from typing import Optional

from core.config import settings

_memory: dict[str, tuple[float, str]] = {}


def _redis():
    if not settings.use_redis:
        return None
    import redis  # 延迟导入，演示环境无依赖也不报错
    try:
        return redis.Redis.from_url(settings.redis_url, socket_connect_timeout=2)
    except Exception:
        return None


def get(key: str) -> Optional[dict]:
    r = _redis()
    if r is not None:
        v = r.get(key)
        return json.loads(v) if v else None
    item = _memory.get(key)
    if item and item[0] > time.time():
        return json.loads(item[1])
    _memory.pop(key, None)
    return None


def set(key: str, value: dict, ttl: int = 300) -> None:
    payload = json.dumps(value, ensure_ascii=False)
    r = _redis()
    if r is not None:
        r.setex(key, ttl, payload)
        return
    _memory[key] = (time.time() + ttl, payload)
