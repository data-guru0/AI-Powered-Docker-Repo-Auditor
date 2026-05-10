import time
import logging
from fastapi import HTTPException, Depends
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            from app.core.config import settings
            _redis_client = redis.from_url(
                settings.REDIS_URL, decode_responses=True, socket_timeout=2
            )
        except Exception as exc:
            logger.warning("Redis unavailable for rate limiting: %s", exc)
            return None
    return _redis_client


def _check_limit(user_id: str, action: str, limit: int, window_seconds: int) -> None:
    client = _get_redis()
    if client is None:
        return  # Fail open — never block users if Redis is down

    key = f"ratelimit:{action}:{user_id}"
    now = time.time()

    try:
        pipe = client.pipeline()
        pipe.zremrangebyscore(key, 0, now - window_seconds)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window_seconds)
        results = pipe.execute()
        count = results[2]

        if count > limit:
            window_h = window_seconds // 3600
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: max {limit} {action}s per {window_h}h. Try again later.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Rate limit check error (fail-open): %s", exc)


def scan_rate_limit(user: dict = Depends(get_current_user)) -> dict:
    _check_limit(user["user_id"], "scan", limit=5, window_seconds=3600)
    return user


def chat_rate_limit(user: dict = Depends(get_current_user)) -> dict:
    _check_limit(user["user_id"], "chat", limit=20, window_seconds=3600)
    return user
