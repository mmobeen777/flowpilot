import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.user.models import Organization

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Organization)
def create_free_subscription(sender, instance, created, **kwargs):
    """Auto-assign Free plan when a new Organization is created."""
    if not created:
        return

    from apps.billing.models import Plan, Subscription

    try:
        free_plan = Plan.objects.get(tier=Plan.Tier.FREE)
    except Plan.DoesNotExist:
        logger.warning(
            "Free plan not found — run python manage.py seed_plans. "
            "Org %s has no subscription.", instance.id
        )
        return

    Subscription.objects.create(
        organization=instance,
        plan=free_plan,
        status=Subscription.Status.ACTIVE,
    )
    logger.info("Free subscription created for org %s", instance.id)
