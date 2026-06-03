import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.user.models import Organization

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Organization)
def create_free_subscription(sender, instance, created, **kwargs):
    if not created:
        return

    from apps.billing.models import Plan, Subscription
    from apps.utils.Stripe import create_customer

    # 1. Create Stripe customer
    stripe_customer_id = ""
    try:
        stripe_customer_id = create_customer(instance)
    except Exception as exc:
        logger.error("Stripe customer creation failed for org %s: %s", instance.id, exc)

    # 2. Assign Free plan subscription
    try:
        free_plan = Plan.objects.get(tier=Plan.Tier.FREE)
    except Plan.DoesNotExist:
        logger.warning("Free plan not found — run seed_plans. Org %s has no subscription.", instance.id)
        return

    Subscription.objects.create(
        organization=instance,
        plan=free_plan,
        status=Subscription.Status.ACTIVE,
        stripe_customer_id=stripe_customer_id,
    )
    logger.info("Free subscription + Stripe customer created for org %s", instance.id)
