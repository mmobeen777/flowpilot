import secrets
from django.db import models
from django.conf import settings

from ..utils.Models import BaseModel
from ..utils.Fields import CharIDField


class Invitation(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        EXPIRED = "expired", "Expired"

    id = CharIDField(primary_key=True, prefix='inv_')
    organization = models.ForeignKey("user.Organization", on_delete=models.CASCADE, related_name="invitations")
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name="sent_invitations")

    email = models.EmailField()
    role = models.CharField(max_length=20, default="member")
    token = models.CharField(max_length=64, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    expires_at = models.DateTimeField()

    class Meta:
        unique_together = ["organization", "email"]
        db_table = "invitations"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(48)
        super().save(*args, **kwargs)

    def __str__(self):
        """Return string representation of Invitation model."""
        return f"{self.email} → {self.organization}"
