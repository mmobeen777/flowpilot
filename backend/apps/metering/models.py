from django.db import models

from ..utils.Models import BaseModel
from ..utils.Fields import CharIDField


class UsageRecord(BaseModel):

    id = CharIDField(primary_key=True, prefix="usg_")
    organization = models.ForeignKey("user.Organization", on_delete=models.CASCADE, related_name="usage_records")

    date = models.DateField()
    call_count = models.PositiveIntegerField(default=0)
    flushed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "usage_record"
        unique_together = ["organization", "date"]
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["organization", "date"]),
        ]

    def __str__(self):
        return f"{self.organization} — {self.date} — {self.call_count} calls"

    @classmethod
    def record(cls, org, date, count: int):
        """
        Upsert a usage record for a given org and date.
        Uses update_or_create so re-running the flush is safe (idempotent).
        """
        obj, created = cls.objects.update_or_create(
            organization=org,
            date=date,
            defaults={"call_count": models.F("call_count") + count},
        )
        return obj
