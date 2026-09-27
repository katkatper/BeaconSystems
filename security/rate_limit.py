import hashlib
import logging
import threading
import time

from fastapi import HTTPException, Request, status
from redis import Redis
from redis.exceptions import RedisError

from config.settings import IS_PRODUCTION, RATE_LIMIT_REDIS_URL


logger = logging.getLogger("beacon.security")
_redis_client = Redis.from_url(RATE_LIMIT_REDIS_URL) if RATE_LIMIT_REDIS_URL else None
_local_counts: dict[str, tuple[int, int]] = {}
_local_lock = threading.Lock()


def client_address(request: Request) -> str:
    """Return the peer address normalized by Uvicorn's trusted-proxy handling."""
    return request.client.host if request.client else "unknown"


def _rate_limit_key(namespace: str, identifier: str, window: int, now: int) -> tuple[str, int]:
    bucket = now // window
    digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()
    return f"beacon:rate-limit:{namespace}:{digest}:{bucket}", bucket


def _increment_local(key: str, expires_at: int, now: int) -> int:
    with _local_lock:
        for expired_key, (_, expiration) in list(_local_counts.items()):
            if expiration <= now:
                del _local_counts[expired_key]
        count = _local_counts.get(key, (0, expires_at))[0] + 1
        _local_counts[key] = (count, expires_at)
        return count


def enforce_rate_limit(
    request: Request,
    *,
    namespace: str,
    identifier: str,
    limit: int,
    window_seconds: int,
) -> None:
    now = int(time.time())
    key, bucket = _rate_limit_key(namespace, identifier, window_seconds, now)
    retry_after = window_seconds - (now % window_seconds)

    if _redis_client is not None:
        try:
            pipeline = _redis_client.pipeline(transaction=True)
            pipeline.incr(key)
            pipeline.expire(key, window_seconds + 1)
            count = int(pipeline.execute()[0])
        except RedisError as exc:
            logger.exception("Shared authentication rate limiter is unavailable")
            if IS_PRODUCTION:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication protection is temporarily unavailable",
                    headers={"Retry-After": "5"},
                ) from exc
            count = _increment_local(key, (bucket + 1) * window_seconds, now)
    else:
        count = _increment_local(key, (bucket + 1) * window_seconds, now)

    if count > limit:
        logger.warning(
            "Authentication rate limit exceeded",
            extra={"rate_limit_namespace": namespace, "client": client_address(request)},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )
