import io, csv, json
from datetime import date

from apps.metering.models import UsageRecord


def _get_records(org, date_from: date, date_to: date):
    """Shared queryset used by both exporters."""
    return (
        UsageRecord.objects
        .filter(
            organization=org,
            date__gte=date_from,
            date__lte=date_to,
        )
        .order_by("date")
        .values("date", "call_count")
    )


def build_csv(org, date_from: date, date_to: date) -> tuple[bytes, int]:
    """
    Returns (csv_bytes, row_count).
    """
    records = list(_get_records(org, date_from, date_to))

    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow([
        "date",
        "calls",
        "organization",
        "org_slug",
    ])

    for r in records:
        writer.writerow([
            r["date"].isoformat(),
            r["call_count"],
            org.name,
            org.slug,
        ])

    return buffer.getvalue().encode("utf-8"), len(records)


def build_json(org, date_from: date, date_to: date) -> tuple[bytes, int]:
    """
    Returns (json_bytes, row_count).
    """
    records = list(_get_records(org, date_from, date_to))

    payload = {
        "organization": org.name,
        "org_slug": org.slug,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "total_calls": sum(r["call_count"] for r in records),
        "rows": [
            {
                "date": r["date"].isoformat(),
                "calls": r["call_count"],
            }
            for r in records
        ],
    }

    content = json.dumps(payload, indent=2).encode("utf-8")
    return content, len(records)
