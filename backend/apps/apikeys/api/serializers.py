import ipaddress

from django.utils import timezone
from rest_framework import serializers
from ..models import APIKey


def validate_ip_entries(value):
    """
    Ensure every entry is a valid IP address or CIDR range (v4 or v6).
    Returns the normalised list.
    """
    if value in (None, ""):
        return []

    if not isinstance(value, list):
        raise serializers.ValidationError("allowed_ips must be a list of IPs or CIDR ranges.")

    cleaned = []
    for entry in value:
        if not isinstance(entry, str):
            raise serializers.ValidationError(f"Invalid entry: {entry!r} is not a string.")
        entry = entry.strip()
        try:
            ipaddress.ip_network(entry, strict=False)
        except ValueError:
            raise serializers.ValidationError(f"'{entry}' is not a valid IP address or CIDR range.")
        cleaned.append(entry)

    return cleaned


class APIKeyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    allowed_ips = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )

    def validate_expires_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError("Expiry must be in the future.")

        return value

    def validate_allowed_ips(self, value):
        return validate_ip_entries(value)


class APIKeySerializer(serializers.ModelSerializer):
    """
    Safe serializer — never exposes hashed_key.
    The raw key is only returned once via APIKeyCreatedSerializer.
    """
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)

    class Meta:
        model = APIKey
        fields = ["id", "name", "prefix", "is_active", "created_by_email", "last_used_at",
                  "expires_at", "allowed_ips", "created_at"]
        read_only_fields = fields


class APIKeyCreatedSerializer(APIKeySerializer):
    """
    Returned only on creation and rotation.
    Includes the raw key — shown once, never again.
    """
    raw_key = serializers.CharField(read_only=True)

    class Meta(APIKeySerializer.Meta):
        fields = APIKeySerializer.Meta.fields + ["raw_key"]


class APIKeyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIKey
        fields = ["name", "allowed_ips"]

    def validate_allowed_ips(self, value):
        return validate_ip_entries(value)
