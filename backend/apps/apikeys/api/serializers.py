from django.utils import timezone
from rest_framework import serializers
from ..models import APIKey


class APIKeyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate_expires_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError("Expiry must be in the future.")

        return value


class APIKeySerializer(serializers.ModelSerializer):
    """
    Safe serializer — never exposes hashed_key.
    The raw key is only returned once via APIKeyCreatedSerializer.
    """
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)

    class Meta:
        model = APIKey
        fields = ["id", "name", "prefix", "is_active", "created_by_email", "last_used_at", "expires_at", "created_at"]
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
        fields = ["name"]
