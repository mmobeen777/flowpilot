from django.core.cache import cache
from django.conf import settings


CACHE_TTL = 60 * 5


def cached_query(key: str, fn, *args, **kwargs):
    """
    Generic cache wrapper.
    Usage:
        data = cached_query(f"usage:{org_id}:daily", get_daily_usage, org, days=30)
    """
    result = cache.get(key)
    if result is None:
        result = fn(*args, **kwargs)
        cache.set(key, result, CACHE_TTL)
    return result


def bust_org_cache(org_id: str):
    """
    Call this after any write that would invalidate stats data.
    Currently called after plan upgrades and subscription changes.
    """
    patterns = [
        f"analytics:{org_id}:daily",
        f"analytics:{org_id}:summary",
        f"analytics:{org_id}:quota_trend",
        f"analytics:{org_id}:monthly",
        f"analytics:{org_id}:peak",
    ]
    cache.delete_many(patterns)
