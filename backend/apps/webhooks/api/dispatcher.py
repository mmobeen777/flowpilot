import logging
from ..models import WebhookEndpoint, WebhookDelivery
from .signing import build_payload
from apps.tasks import deliver_webhook

logger = logging.getLogger(__name__)


def fire_event(org, event_type: str, data: dict):
    """
    Find all active endpoints subscribed to this event,
    create a WebhookDelivery per endpoint, and enqueue delivery tasks.

    Safe to call anywhere — never raises, never blocks.
    """
    try:
        endpoints = WebhookEndpoint.objects.filter(
            organization=org,
            is_active=True,
        )

        if not endpoints.exists():
            return

        payload = build_payload(
            event_type=event_type,
            data=data,
            org_id=str(org.id),
        )

        for endpoint in endpoints:
            if not endpoint.is_subscribed(event_type):
                continue

            delivery = WebhookDelivery.objects.create(
                endpoint=endpoint,
                event_type=event_type,
                payload=payload,
            )

            deliver_webhook.delay(str(delivery.id))
            logger.info(
                "Fired %s to endpoint %s (delivery %s)",
                event_type, endpoint.url, delivery.id,
            )

    except Exception as exc:
        # Never let webhook dispatch crash the caller
        logger.error("fire_event failed for %s on org %s: %s", event_type, org.id, exc)
