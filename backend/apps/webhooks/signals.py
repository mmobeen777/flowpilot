import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import WebhookDelivery

logger = logging.getLogger(__name__)


@receiver(post_save, sender=WebhookDelivery)
def deactivate_endpoint_on_permanent_failure(sender, instance, **kwargs):
    """
    After max retries, mark the endpoint inactive so it stops
    receiving future events until the org re-enables it.
    """
    if instance.status != WebhookDelivery.Status.FAILED:
        return

    endpoint = instance.endpoint
    if not endpoint.is_active:
        return

    # Count how many recent deliveries to this endpoint have permanently failed
    recent_failures = WebhookDelivery.objects.filter(
        endpoint=endpoint,
        status=WebhookDelivery.Status.FAILED,
    ).count()

    if recent_failures >= 3:
        endpoint.is_active = False
        endpoint.save(update_fields=["is_active"])
        logger.warning(
            "Endpoint %s deactivated after %d permanent failures",
            endpoint.url, recent_failures,
        )
