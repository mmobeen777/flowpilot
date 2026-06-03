import logging, stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from ..models import Subscription

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    # 1. Verify the signature — reject anything that doesn't match
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.SignatureVerificationError) as exc:
        logger.warning("Webhook signature verification failed: %s", exc)
        return HttpResponse(status=400)

    event_type = event["type"]
    data = event["data"]["object"]

    logger.info("Stripe webhook received: %s", event_type)

    # 2. Route to the appropriate handler
    handlers = {
        "customer.subscription.updated": _handle_subscription_updated,
        "customer.subscription.deleted": _handle_subscription_deleted,
        "invoice.paid": _handle_invoice_paid,
        "invoice.payment_failed": _handle_invoice_payment_failed,
    }

    handler = handlers.get(event_type)
    if handler:
        try:
            handler(data)
        except Exception as exc:
            logger.error("Webhook handler error for %s: %s", event_type, exc)
            # Return 200 anyway — Stripe will retry on 5xx, not 4xx
            # Returning 500 here causes Stripe to retry indefinitely

    # Always return 200 to acknowledge receipt
    return HttpResponse(status=200)


def _handle_subscription_updated(data):
    stripe_sub_id = data["id"]
    new_status = data["status"]

    try:
        sub = Subscription.objects.get(stripe_subscription_id=stripe_sub_id)
    except Subscription.DoesNotExist:
        logger.warning("Subscription not found for stripe_id %s", stripe_sub_id)
        return

    status_map = {
        "active": Subscription.Status.ACTIVE,
        "past_due": Subscription.Status.PAST_DUE,
        "canceled": Subscription.Status.CANCELLED,
        "trialing": Subscription.Status.TRIALING,
    }

    if new_status in status_map:
        sub.status = status_map[new_status]

    # Update billing period
    if data.get("current_period_start"):
        from django.utils.dateparse import parse_datetime
        from datetime import datetime, timezone
        sub.current_period_start = datetime.fromtimestamp(
            data["current_period_start"], tz=timezone.utc
        )
        sub.current_period_end = datetime.fromtimestamp(
            data["current_period_end"], tz=timezone.utc
        )

    sub.save(update_fields=["status", "current_period_start", "current_period_end", "updated_at"])
    logger.info("Subscription %s updated to status %s", stripe_sub_id, new_status)


def _handle_subscription_deleted(data):
    stripe_sub_id = data["id"]

    try:
        sub = Subscription.objects.get(stripe_subscription_id=stripe_sub_id)
    except Subscription.DoesNotExist:
        return

    sub.status = Subscription.Status.CANCELLED
    sub.save(update_fields=["status", "updated_at"])
    logger.info("Subscription %s cancelled", stripe_sub_id)


def _handle_invoice_paid(data):
    """Invoice paid — ensure subscription is marked active."""
    stripe_customer_id = data.get("customer")
    if not stripe_customer_id:
        return

    try:
        sub = Subscription.objects.get(stripe_customer_id=stripe_customer_id)
    except Subscription.DoesNotExist:
        return

    if sub.status == Subscription.Status.PAST_DUE:
        sub.status = Subscription.Status.ACTIVE
        sub.save(update_fields=["status", "updated_at"])
        logger.info("Subscription for customer %s restored to active after payment", stripe_customer_id)


def _handle_invoice_payment_failed(data):
    stripe_customer_id = data.get("customer")
    if not stripe_customer_id:
        return

    try:
        sub = Subscription.objects.get(stripe_customer_id=stripe_customer_id)
    except Subscription.DoesNotExist:
        return

    sub.status = Subscription.Status.PAST_DUE
    sub.save(update_fields=["status", "updated_at"])
    logger.warning("Payment failed for customer %s — subscription marked past_due", stripe_customer_id)
