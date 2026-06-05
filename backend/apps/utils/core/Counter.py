import logging
import redis
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

_redis_client = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
    return _redis_client


def _month_key(org_id: str, dt=None) -> str:
    """org:{org_id}:calls:2025-01"""
    dt = dt or timezone.now()
    return f"org:{org_id}:calls:{dt.strftime('%Y-%m')}"


def _day_key(org_id: str, dt=None) -> str:
    """org:{org_id}:calls:2025-01-15"""
    dt = dt or timezone.now()
    return f"org:{org_id}:calls:{dt.strftime('%Y-%m-%d')}"


def increment_usage(org_id: str) -> None:
    """
    Atomically increment both the monthly and daily counters
    for an org. Called on every metered request.
    Uses a pipeline so both INCRs happen in one round trip.
    """
    try:
        r = get_redis()
        now = timezone.now()
        pipe = r.pipeline()
        pipe.incr(_month_key(org_id, now))
        pipe.incr(_day_key(org_id, now))
        pipe.execute()
    except redis.RedisError:
        # Never let a Redis failure break the actual API response
        logger.warning("Redis unavailable — usage not counted for org %s", org_id)


def get_month_count(org_id: str, dt=None) -> int:
    """Current month's call count for an org."""
    try:
        r = get_redis()
        value = r.get(_month_key(org_id, dt))
        return int(value) if value else 0
    except redis.RedisError:
        return 0


def get_day_count(org_id: str, dt=None) -> int:
    """Today's call count for an org."""
    try:
        r = get_redis()
        value = r.get(_day_key(org_id, dt))
        return int(value) if value else 0
    except redis.RedisError:
        return 0


def get_and_reset_month_count(org_id: str, dt=None) -> int:
    """
    Atomically read and delete the monthly counter.
    Returns 0 if the key doesn't exist.
    """
    try:
        r = get_redis()
        value = r.getdel(_month_key(org_id, dt))
        return int(value) if value else 0
    except redis.RedisError:
        return 0


def list_active_org_keys(pattern: str = "org:*:calls:????-??") -> list[str]:
    """
    Scan for all monthly counter keys currently in Redis.
    Used by the billing sync task to find all orgs with usage.
    Uses SCAN not KEYS — safe for production Redis.
    """
    try:
        r = get_redis()
        keys = []
        cursor = 0
        while True:
            cursor, batch = r.scan(cursor, match=pattern, count=100)
            keys.extend(batch)
            if cursor == 0:
                break
        return keys
    except redis.RedisError:
        return []


