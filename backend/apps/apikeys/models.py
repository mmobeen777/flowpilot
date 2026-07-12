import uuid
import hashlib
import ipaddress
import secrets
from django.db import models
from django.conf import settings

from ..utils.Models import BaseModel
from ..utils.Fields import CharIDField


class APIKey(BaseModel):
    id = CharIDField(primary_key=True, prefix="key_")
    organization = models.ForeignKey("user.Organization", on_delete=models.CASCADE, related_name="api_keys")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_api_keys")

    name = models.CharField(max_length=100, help_text="Human label, e.g. 'Production key'")
    prefix = models.CharField(max_length=10, editable=False)
    hashed_key = models.CharField(max_length=128, unique=True, editable=False)

    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    allowed_ips = models.JSONField(
        default=list,
        blank=True,
        help_text="List of IPs / CIDR ranges this key may be used from. "
                  "Empty means no restriction.",
    )

    class Meta:
        db_table = "api_keys"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.prefix}...)"

    @classmethod
    def create_key(cls, organization, created_by, name, expires_at=None, allowed_ips=None):
        """
        Generate a new key, store its hash, and return
        (instance, raw_key). raw_key is shown once and discarded.
        """
        raw_key = generate_key()
        prefix = raw_key[:10]          # e.g. "fp_abc123de" — shown in UI for identification
        hashed = hash_key(raw_key)

        instance = cls.objects.create(
            organization=organization,
            created_by=created_by,
            name=name,
            prefix=prefix,
            hashed_key=hashed,
            expires_at=expires_at,
            allowed_ips=allowed_ips or [],
        )
        return instance, raw_key

    def is_ip_allowed(self, ip: str) -> bool:
        """
        Return True if `ip` is permitted to use this key.

        An empty allowed_ips list means the key is unrestricted.
        Each entry may be a single address (e.g. "203.0.113.7") or a
        CIDR range (e.g. "203.0.113.0/24"), IPv4 or IPv6.
        """
        if not self.allowed_ips:
            return True

        if not ip:
            return False

        try:
            client = ipaddress.ip_address(ip)
        except ValueError:
            return False

        for entry in self.allowed_ips:
            try:
                if client in ipaddress.ip_network(entry, strict=False):
                    return True
            except ValueError:
                continue  # Skip malformed entries rather than failing open

        return False

    @classmethod
    def authenticate(cls, raw_key: str):
        """
        Given a raw key from a request header, return the APIKey
        instance if valid and active. Returns None otherwise.
        """
        if not raw_key or not raw_key.startswith("fp_"):
            return None

        hashed = hash_key(raw_key)

        try:
            key = cls.objects.select_related("organization", "created_by").get(hashed_key=hashed, is_active=True)

        except cls.DoesNotExist:
            return None

        if key.expires_at:
            from django.utils import timezone
            if key.expires_at < timezone.now():
                return None

        # Update last_used_at without triggering full save
        from django.utils import timezone
        cls.objects.filter(pk=key.pk).update(last_used_at=timezone.now())

        return key


def generate_key():
    """Generate a random 40-byte URL-safe key with a fp_ prefix."""
    return f"fp_{secrets.token_urlsafe(40)}"


def hash_key(raw_key: str) -> str:
    """One-way BLAKE2b hash of the raw key for storage."""
    return hashlib.blake2b(raw_key.encode(), digest_size=32).hexdigest()
