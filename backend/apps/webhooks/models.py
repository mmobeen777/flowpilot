import hashlib, hmac, secrets
from django.db import models

from apps.utils.Models import BaseModel
from apps.utils.Fields import CharIDField


class WebhookEndpoint(BaseModel):
    id = CharIDField(primary_key=True, prefix="web_end_")
    organization = models.ForeignKey("user.Organization", on_delete=models.CASCADE, related_name="webhook_endpoints")
    url = models.URLField(max_length=500)
    # Signing secret — shown once on creation, stored hashed
    secret = models.CharField(max_length=128, editable=False)
    description = models.CharField(max_length=200, blank=True)

    # Which events this endpoint subscribes to.
    # Empty list = all events.
    subscribed_events = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "webhook_endpoints"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.organization} → {self.url}"

    @classmethod
    def create_endpoint(cls, organization, url, description="", events=None):
        """
        Generate a signing secret, store it, and return
        (instance, raw_secret). Raw secret shown once.
        """
        raw_secret = f"whsec_{secrets.token_urlsafe(32)}"
        instance = cls.objects.create(
            organization=organization,
            url=url,
            secret=raw_secret,        # stored as plaintext here — unlike API keys,
            description=description,  # webhook secrets need to be retrievable to sign
            subscribed_events=events or [],
        )
        return instance, raw_secret

    def is_subscribed(self, event_type: str) -> bool:
        """Empty subscribed_events means subscribed to everything."""
        if not self.subscribed_events:
            return True
        return event_type in self.subscribed_events

    def sign_payload(self, timestamp: str, raw_body: str) -> str:
        """
        HMAC-SHA256 signature over '{timestamp}.{body}'.
        Receivers verify this to confirm the payload is genuine.
        """
        message = f"{timestamp}.{raw_body}"
        return hmac.new(
            self.secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()


class WebhookDelivery(BaseModel):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        RETRYING = "retrying", "Retrying"

    id = CharIDField(primary_key=True, prefix="web_del_")
    endpoint = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE, related_name="deliveries")
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    response_status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    error_message = models.TextField(blank=True)

    attempt_count = models.PositiveIntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "webhook_delivery"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["endpoint", "status"]),
            models.Index(fields=["endpoint", "event_type"]),
        ]

    def __str__(self):
        return f"{self.event_type} → {self.endpoint.url} ({self.status})"
