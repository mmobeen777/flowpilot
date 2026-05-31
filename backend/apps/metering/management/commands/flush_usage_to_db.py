from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.user.models import Organization
from apps.utils.core.Counter import list_active_org_keys, get_and_reset_month_count
from apps.metering.models import UsageRecord


class Command(BaseCommand):
    help = "Flush Redis usage counters to Postgres UsageRecord rows."

    def handle(self, *args, **options):
        today = timezone.now().date()
        keys = list_active_org_keys()

        if not keys:
            self.stdout.write("No active counters found in Redis.")
            return

        flushed = 0
        for key in keys:
            # key format: org:{id}:calls:{YYYY-MM}
            try:
                parts = key.split(":")
                org_id = parts[1]
                period = parts[3]          # e.g. "2025-01"
            except IndexError:
                self.stderr.write(f"Skipping malformed key: {key}")
                continue

            count = get_and_reset_month_count(org_id)
            if count == 0:
                continue

            try:
                org = Organization.objects.get(id=org_id)
            except Organization.DoesNotExist:
                self.stderr.write(f"Org {org_id} not found, skipping.")
                continue

            UsageRecord.record(org=org, date=today, count=count)
            flushed += 1
            self.stdout.write(
                f"  {org.name}: +{count} calls → {period}"
            )

        self.stdout.write(
            self.style.SUCCESS(f"Flushed {flushed} org counters to DB.")
        )
