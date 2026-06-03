from django.core.management.base import BaseCommand
from apps.billing.models import Plan


PLANS = [
    {
        "name": "Free",
        "tier": Plan.Tier.FREE,
        "monthly_call_limit": 1000,
        "max_api_keys": 2,
        "max_members": 1,
        "can_use_webhooks": False,
        "can_use_analytics": False,
        "can_export_data": False,
    },
    {
        "name": "Starter",
        "tier": Plan.Tier.STARTER,
        "monthly_call_limit": 50000,
        "max_api_keys": 5,
        "max_members": 5,
        "can_use_webhooks": True,
        "can_use_analytics": False,
        "can_export_data": False,
        "stripe_price_id": "price_1TeGom0apCLtFQSEPTqZ8PtZ"  # should be in env maybe later
    },
    {
        "name": "Pro",
        "tier": Plan.Tier.PRO,
        "monthly_call_limit": 500000,
        "max_api_keys": 20,
        "max_members": 25,
        "can_use_webhooks": True,
        "can_use_analytics": True,
        "can_export_data": True,
        "stripe_price_id": "price_1TeG7A0apCLtFQSERazrLHk0"
    },
    {
        "name": "Enterprise",
        "tier": Plan.Tier.ENTERPRISE,
        "monthly_call_limit": None,        # unlimited
        "max_api_keys": 100,
        "max_members": 1000,
        "can_use_webhooks": True,
        "can_use_analytics": True,
        "can_export_data": True,
        "stripe_price_id": "price_1TeGpe0apCLtFQSEXlqUYqw0"
    },
]


class Command(BaseCommand):
    help = "Seed the Plan table with default plans. Safe to re-run."

    def handle(self, *args, **options):
        for data in PLANS:
            plan, created = Plan.objects.update_or_create(
                tier=data["tier"],
                defaults=data,
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action}: {plan}")

        self.stdout.write(self.style.SUCCESS("Plans seeded successfully."))
