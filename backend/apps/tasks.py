import logging, json, requests
from celery import shared_task
from datetime import datetime, timezone, timedelta
from django.utils import timezone as django_timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="flush_usage_and_report",
)
def flush_usage_and_report(self):
    """
    Nightly task — runs at midnight UTC.

    For every org with Redis usage counters:
      1. GETDEL the monthly counter (atomic read + reset)
      2. Write a UsageRecord to Postgres
      3. Report usage to Stripe

    Idempotent: if it runs twice, UsageRecord.record() adds to
    existing counts and Stripe receives the same quantity (set, not increment).
    """
    from apps.utils.core.Counter import list_active_org_keys, get_redis
    from apps.metering.models import UsageRecord
    from apps.user.models import Organization
    from apps.billing.models import Subscription
    from apps.utils.Stripe import report_usage

    today = django_timezone.now().date()
    yesterday = today - timedelta(days=1)

    # Scan Redis for all daily keys from yesterday
    # Pattern: org:{uuid}:calls:{YYYY-MM-DD}
    pattern = f"org:*:calls:{yesterday.strftime('%Y-%m-%d')}"
    keys = list_active_org_keys(pattern=pattern)

    if not keys:
        logger.info("flush_usage_and_report: no usage keys for %s", yesterday)
        return {"flushed": 0, "reported": 0}

    flushed = 0
    reported = 0
    errors = []

    for key in keys:
        # key format: org:{uuid}:calls:{YYYY-MM-DD}
        try:
            parts = key.split(":")
            org_id = parts[1]
        except IndexError:
            logger.warning("Malformed Redis key: %s", key)
            continue

        # Step 1 — atomic read + delete
        try:
            r = get_redis()
            raw = r.getdel(key)
            count = int(raw) if raw else 0
        except Exception as exc:
            logger.error("Redis GETDEL failed for key %s: %s", key, exc)
            errors.append(key)
            continue

        if count == 0:
            continue

        # Step 2 — write to Postgres
        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            logger.warning("Org %s not found, skipping.", org_id)
            continue

        UsageRecord.record(org=org, date=yesterday, count=count)
        flushed += 1

        # Step 3 — report to Stripe
        try:
            subscription = Subscription.objects.get(
                organization=org,
                status__in=["active", "trialing", "past_due"],
            )
        except Subscription.DoesNotExist:
            logger.info("No active subscription for org %s, skipping Stripe report.", org_id)
            continue

        if not subscription.stripe_subscription_item_id:
            logger.info("No stripe_subscription_item_id for org %s, skipping.", org_id)
            continue

        period_timestamp = int(datetime(yesterday.year, yesterday.month,
                                        yesterday.day, 23, 59, 59, tzinfo=timezone.utc).timestamp())

        try:
            report_usage(
                stripe_subscription_item_id=subscription.stripe_subscription_item_id,
                quantity=count,
                timestamp=period_timestamp,
            )
            reported += 1
            logger.info("Reported %d calls for org %s (%s) to Stripe", count, org.name, yesterday)
        except Exception as exc:
            logger.error("Stripe usage report failed for org %s: %s", org_id, exc)
            errors.append(f"stripe:{org_id}")

    result = {"flushed": flushed, "reported": reported, "errors": errors}
    logger.info("flush_usage_and_report complete: %s", result)

    if errors:
        # Raise so Celery marks the task as failed and retries
        raise self.retry(
            exc=Exception(f"Partial failure: {errors}"),
            countdown=300,
        )

    return result


@shared_task(
    name="monthly_usage_rollup",
    max_retries=2,
)
def monthly_usage_rollup():
    """
    Runs on the 1st of each month at 01:00 UTC.
    Catches any remaining monthly counter that the nightly task might have missed.
    """
    from apps.metering.models import UsageRecord
    from apps.user.models import Organization
    from apps.utils.core.Counter import list_active_org_keys, get_redis

    today = django_timezone.now().date()
    first_of_this_month = today.replace(day=1)
    last_month = first_of_this_month - timedelta(days=1)
    month_str = last_month.strftime("%Y-%m")

    pattern = f"org:*:calls:{month_str}"
    keys = list_active_org_keys(pattern=pattern)

    if not keys:
        logger.info("monthly_usage_rollup: no leftover keys for %s", month_str)
        return

    r = get_redis()
    for key in keys:
        try:
            parts = key.split(":")
            org_id = parts[1]
            raw = r.getdel(key)
            count = int(raw) if raw else 0
        except Exception as exc:
            logger.error("monthly_rollup error for key %s: %s", key, exc)
            continue

        if count == 0:
            continue

        try:
            org = Organization.objects.get(id=org_id)
            UsageRecord.record(org=org, date=last_month, count=count)
            logger.info("Monthly rollup: %d calls for org %s (%s)", count, org.name, month_str)
        except Organization.DoesNotExist:
            continue


@shared_task(
    name="analytics.generate_export",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def generate_export(self, export_id: str):
    """
    Background task — builds the export file and writes it back
    to the Export row. The HTTP polling endpoint checks status.
    """
    from apps.stats.models import Export
    from apps.stats.api.exports import build_csv, build_json

    try:
        export = Export.objects.select_related("organization").get(id=export_id)
    except Export.DoesNotExist:
        logger.error("Export %s not found", export_id)
        return

    export.status = Export.Status.PROCESSING
    export.save(update_fields=["status"])

    try:
        org = export.organization

        if export.format == Export.Format.CSV:
            content, row_count = build_csv(org, export.date_from, export.date_to)
            file_name = f"{org.slug}_usage_{export.date_from}_{export.date_to}.csv"
        else:
            content, row_count = build_json(org, export.date_from, export.date_to)
            file_name = f"{org.slug}_usage_{export.date_from}_{export.date_to}.json"

        # In real project send email instead of polling, maybe later for this too
        export.file_content = content
        export.file_name = file_name
        export.row_count = row_count
        export.status = Export.Status.COMPLETE
        export.completed_at = timezone.now()
        export.save(update_fields=[
            "file_content", "file_name", "row_count",
            "status", "completed_at",
        ])

        logger.info(
            "Export %s complete — %d rows, %d bytes",
            export_id, row_count, len(content),
        )

    except Exception as exc:
        logger.error("Export %s failed: %s", export_id, exc)
        export.status = Export.Status.FAILED
        export.error_message = str(exc)
        export.save(update_fields=["status", "error_message"])
        raise self.retry(exc=exc)


# Exponential backoff delays in seconds for each retry attempt
RETRY_DELAYS = [60, 300, 1800, 7200, 86400]  # 1m, 5m, 30m, 2h, 24h
DELIVERY_TIMEOUT = 10
@shared_task(
    name="webhooks.deliver",
    bind=True,
    max_retries=len(RETRY_DELAYS),
)
def deliver_webhook(self, delivery_id: str):
    from apps.webhooks.models import WebhookDelivery
    from apps.webhooks.api.signing import build_headers

    try:
        delivery = WebhookDelivery.objects.select_related("endpoint").get(
            id=delivery_id
        )
    except WebhookDelivery.DoesNotExist:
        logger.error("WebhookDelivery %s not found", delivery_id)
        return

    endpoint = delivery.endpoint

    if not endpoint.is_active:
        delivery.status = WebhookDelivery.Status.FAILED
        delivery.error_message = "Endpoint deactivated."
        delivery.save(update_fields=["status", "error_message"])
        return

    body = json.dumps(delivery.payload)
    headers = build_headers(endpoint.secret, body)
    headers["X-FlowPilot-Event"] = delivery.event_type

    delivery.attempt_count += 1
    delivery.status = WebhookDelivery.Status.RETRYING
    delivery.save(update_fields=["attempt_count", "status"])

    try:
        response = requests.post(
            endpoint.url,
            data=body,
            headers=headers,
            timeout=DELIVERY_TIMEOUT,
        )

        delivery.response_status_code = response.status_code
        # Store first 500 chars of response body for debugging
        delivery.response_body = response.text[:500]

        if 200 <= response.status_code < 300:
            delivery.status = WebhookDelivery.Status.SUCCESS
            delivery.delivered_at = timezone.now()
            delivery.save(update_fields=[
                "response_status_code", "response_body",
                "status", "delivered_at",
            ])
            logger.info(
                "Webhook %s delivered to %s — HTTP %s",
                delivery_id, endpoint.url, response.status_code,
            )
        else:
            _schedule_retry(self, delivery, f"HTTP {response.status_code}")

    except requests.Timeout:
        _schedule_retry(self, delivery, "Request timed out")

    except requests.RequestException as exc:
        _schedule_retry(self, delivery, str(exc))


def _schedule_retry(task, delivery, reason: str):
    from apps.webhooks.models import WebhookDelivery

    attempt = delivery.attempt_count
    if attempt <= len(RETRY_DELAYS):
        delay = RETRY_DELAYS[attempt - 1]
        delivery.next_retry_at = timezone.now() + timedelta(seconds=delay)
        delivery.status = WebhookDelivery.Status.RETRYING
        delivery.error_message = reason
        delivery.save(update_fields=[
            "status", "error_message", "next_retry_at",
            "response_status_code", "response_body",
        ])
        logger.warning(
            "Webhook %s failed (%s) — retry in %ds",
            delivery.id, reason, delay,
        )
        raise task.retry(countdown=delay)
    else:
        delivery.status = WebhookDelivery.Status.FAILED
        delivery.error_message = f"Max retries exceeded. Last error: {reason}"
        delivery.save(update_fields=[
            "status", "error_message",
            "response_status_code", "response_body",
        ])
        logger.error(
            "Webhook %s permanently failed after %d attempts",
            delivery.id, attempt,
        )
