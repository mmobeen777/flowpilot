from django.db import models
from django.conf import settings

from apps.utils.Models import BaseModel
from apps.utils.Fields import CharIDField


class Export(BaseModel):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETE = "complete", "Complete"
        FAILED = "failed", "Failed"

    class Format(models.TextChoices):
        CSV = "csv", "CSV"
        JSON = "json", "JSON"

    id = CharIDField(primary_key=True, prefix="exp_")
    organization = models.ForeignKey("user.Organization", on_delete=models.CASCADE, related_name="exports")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                     related_name="exports")

    format = models.CharField(max_length=10, choices=Format.choices, default=Format.CSV)
    date_from = models.DateField()
    date_to = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    row_count = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    # Sould have used S3 maybe later
    file_content = models.BinaryField(null=True, blank=True, editable=False)
    file_name = models.CharField(max_length=200, blank=True)

    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "exports"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.organization} — {self.format} export ({self.status})"
