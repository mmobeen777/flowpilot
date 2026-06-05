from django.db.models import Sum
from django.utils import timezone
from datetime import date, timedelta

from apps.apikeys.models import APIKey
from apps.metering.models import UsageRecord
from apps.utils.core.Counter import get_day_count, get_month_count


def get_daily_usage(org, days: int = 30) -> list[dict]:
    """
    Returns a list of {date, calls} dicts for the last N days.
    Merges Postgres historical records with today's live Redis count.
    """
    today = timezone.now().date()
    start = today - timedelta(days=days - 1)

    records = (
        UsageRecord.objects
        .filter(organization=org, date__gte=start, date__lt=today)
        .values("date")
        .annotate(calls=Sum("call_count"))
        .order_by("date")
    )

    historical = {r["date"].isoformat(): r["calls"] for r in records}

    result = []
    for i in range(days):
        day = start + timedelta(days=i)
        iso = day.isoformat()
        if day == today:
            calls = get_day_count(str(org.id))
        else:
            calls = historical.get(iso, 0)
        result.append({"date": iso, "calls": calls})

    return result


def get_usage_summary(org) -> dict:
    """
    Returns today, this week, this month, and all-time totals.
    Today and this month come from Redis (live); the rest from Postgres.
    """
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())

    org_id = str(org.id)

    today_count = get_day_count(org_id)
    month_count = get_month_count(org_id)

    week_historical = (
        UsageRecord.objects
        .filter(organization=org, date__gte=week_start, date__lt=today)
        .aggregate(total=Sum("call_count"))["total"] or 0
    )

    all_time = (
        UsageRecord.objects
        .filter(organization=org)
        .aggregate(total=Sum("call_count"))["total"] or 0
    )

    return {
        "today": today_count,
        "this_week": week_historical + today_count,
        "this_month": month_count,
        "all_time": all_time + month_count,
    }


def get_quota_trend(org, days: int = 30) -> list[dict]:
    """
    Daily usage vs plan limit for the last N days.
    Returns {date, calls, limit, percent} per day.
    """
    try:
        limit = org.subscription.plan.monthly_call_limit
    except AttributeError:
        limit = None

    daily = get_daily_usage(org, days=days)

    return [
        {
            "date": row["date"],
            "calls": row["calls"],
            "limit": limit,
            "percent": round((row["calls"] / limit) * 100, 1) if limit else None,
        }
        for row in daily
    ]


def get_top_api_keys(org, days: int = 30, limit: int = 10) -> list[dict]:
    """
    Returns the most-used API keys by last_used_at recency and
    estimated call share, ordered by last_used_at descending.

    Note: per-key call counts require a separate UsageByKey model
    (Day 9 extension). For now this returns key metadata sorted
    by recent activity — accurate and useful without extra storage.
    """
    keys = (
        APIKey.objects
        .filter(organization=org, is_active=True)
        .select_related("created_by")
        .order_by("-last_used_at")[:limit]
    )

    return [
        {
            "id": str(k.id),
            "name": k.name,
            "prefix": k.prefix,
            "created_by": k.created_by.email if k.created_by else None,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "created_at": k.created_at.isoformat(),
        }
        for k in keys
    ]


def get_peak_usage_day(org, days: int = 30):
    """Returns the single highest-call day in the last N days."""
    today = timezone.now().date()
    start = today - timedelta(days=days)

    result = (
        UsageRecord.objects
        .filter(organization=org, date__gte=start)
        .order_by("-call_count")
        .values("date", "call_count")
        .first()
    )

    if not result:
        return None

    return {
        "date": result["date"].isoformat(),
        "calls": result["call_count"],
    }


def get_monthly_totals(org, months: int = 6) -> list[dict]:
    """
    Returns month-by-month totals for the last N months.
    Useful for a bar chart on the billing page.
    """
    today = timezone.now().date()
    result = []

    for i in range(months - 1, -1, -1):
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1

        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1)
        else:
            month_end = date(year, month + 1, 1)

        if month_start.month == today.month and month_start.year == today.year:
            # Current month — use live Redis count
            total = get_month_count(str(org.id))
        else:
            total = (
                UsageRecord.objects
                .filter(organization=org, date__gte=month_start, date__lt=month_end)
                .aggregate(total=Sum("call_count"))["total"] or 0
            )

        result.append({
            "month": month_start.strftime("%Y-%m"),
            "label": month_start.strftime("%b %Y"),
            "calls": total,
        })

    return result
