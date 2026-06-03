import stripe, logging
from django.conf import settings


logger = logging.getLogger(__name__)


stripe.api_key = settings.STRIPE_SECRET_KEY


def create_customer(org) -> str:
    """
    Create a Stripe customer for an org and return the customer ID.
    Called once on org creation.
    """
    customer = stripe.Customer.create(
        name=org.name,
        metadata={"org_id": str(org.id), "org_slug": org.slug},
    )
    return customer.id


def create_subscription(stripe_customer_id: str, stripe_price_id: str) -> stripe.Subscription:
    """
    Create a Stripe subscription for a metered price.
    Returns the full subscription object.
    """
    return stripe.Subscription.create(
        customer=stripe_customer_id,
        items=[{"price": stripe_price_id}],
        expand=["latest_invoice.payment_intent"],
    )


def update_subscription_item(stripe_subscription_id: str, new_price_id: str) -> stripe.Subscription:
    """
    Swap a subscription to a new price (plan upgrade/downgrade).
    Prorates automatically unless you pass proration_behavior='none'.
    """
    subscription = stripe.Subscription.retrieve(stripe_subscription_id)
    item_id = subscription["items"]["data"][0]["id"]

    return stripe.Subscription.modify(
        stripe_subscription_id,
        items=[{"id": item_id, "price": new_price_id}],
        proration_behavior="create_prorations",
    )


def cancel_subscription(stripe_subscription_id: str) -> stripe.Subscription:
    """Cancel at period end — customer keeps access until billing cycle ends."""
    return stripe.Subscription.modify(
        stripe_subscription_id,
        cancel_at_period_end=True,
    )


def report_usage(stripe_subscription_item_id: str, quantity: int, timestamp: int) -> None:
    """
    Report metered usage to Stripe. Called by the Celery Beat task (Day 7).
    timestamp should be a Unix timestamp for the period being reported.
    """
    stripe.SubscriptionItem.create_usage_record(
        stripe_subscription_item_id,
        quantity=quantity,
        timestamp=timestamp,
        action="set",   # "set" replaces the value; "increment" adds to it
    )


def get_upcoming_invoice(stripe_customer_id: str) -> dict:
    """Preview what the customer will be charged at next billing cycle."""
    invoice = stripe.Invoice.upcoming(customer=stripe_customer_id)
    return {
        "amount_due": invoice.amount_due,
        "currency": invoice.currency,
        "period_start": invoice.period_start,
        "period_end": invoice.period_end,
        "lines": [
            {
                "description": line.description,
                "quantity": line.quantity,
                "amount": line.amount,
            }
            for line in invoice.lines.data
        ],
    }
