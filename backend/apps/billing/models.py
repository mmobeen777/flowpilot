import uuid
from django.db import models

from ..utils.Models import BaseModel
from ..utils.Fields import CharIDField


class Plan(BaseModel):
    """
    Defines what an org can do.
    Seeded via management command — not created through the API.
    """

    class Tier(models.TextChoices):
        FREE = "free", "Free"
        STARTER = "starter", "Starter"
        PRO = "pro", "Pro"
        ENTERPRISE = "enterprise", "Enterprise"

    id = CharIDField(primary_key=True, prefix="plan_")
    name = models.CharField(max_length=50)
    tier = models.CharField(max_length=20, choices=Tier.choices, unique=True)

    monthly_call_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="NULL means unlimited",
    )
    max_api_keys = models.PositiveIntegerField(default=2)
    max_members = models.PositiveIntegerField(default=3)

    can_use_webhooks = models.BooleanField(default=False)
    can_use_analytics = models.BooleanField(default=False)
    can_export_data = models.BooleanField(default=False)

    stripe_price_id = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "plan"
        ordering = ["monthly_call_limit"]

    def __str__(self):
        limit = self.monthly_call_limit or "unlimited"
        return f"{self.name} ({limit} calls/mo)"

    @property
    def is_unlimited(self):
        return self.monthly_call_limit is None


class Subscription(BaseModel):
    """One subscription per organisation."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAST_DUE = "past_due", "Past Due"
        CANCELLED = "cancelled", "Cancelled"
        TRIALING = "trialing", "Trialing"

    id = CharIDField(primary_key=True, prefix="sub_")
    organization = models.OneToOneField(
        "user.Organization",
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)

    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "subscription"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.organization} — {self.plan.name} ({self.status})"

    @property
    def is_active(self):
        return self.status in (
            self.Status.ACTIVE,
            self.Status.TRIALING,
        )

    def get_monthly_limit(self):
        """Returns None if unlimited."""
        return self.plan.monthly_call_limit

    def has_feature(self, feature: str) -> bool:
        """Check a boolean feature flag on the plan."""
        return getattr(self.plan, feature, False)
