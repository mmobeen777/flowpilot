from django.db import models
from django.conf import settings

from apps.utils.Models import BaseModel
from apps.utils.Fields import CharIDField


class Notification(BaseModel):

    class Type(models.TextChoices):
        INVITATION = "invitation", "Invitation"
        QUOTA_WARNING = "quota_warning", "Quota Warning"
        QUOTA_EXCEEDED = "quota_exceeded", "Quota Exceeded"
        BILLING_RECEIPT = "billing_receipt", "Billing Receipt"
        KEY_ROTATION_ALERT = "key_rotation_alert", "Key Rotation Alert"
        SUBSCRIPTION_UPGRADED = "subscription_upgraded", "Subscription Upgraded"
        SUBSCRIPTION_CANCELLED = "subscription_cancelled", "Subscription Cancelled"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    id = CharIDField(primary_key=True, prefix="ntf")
    recipient_email = models.EmailField()
    notification_type = models.CharField(max_length=50, choices=Type.choices)
    subject = models.CharField(max_length=300)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    resend_message_id = models.CharField(max_length=200, blank=True)
    error_message = models.TextField(blank=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name="notifications")

    organisation = models.ForeignKey("user.Organization", on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="notifications")

    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient_email", "notification_type"]),
            models.Index(fields=["organisation", "created_at"]),
        ]

    def __str__(self):
        return f"{self.notification_type} → {self.recipient_email} ({self.status})"
