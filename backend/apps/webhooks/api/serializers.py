from rest_framework import serializers

from apps.utils.Constants import EVENT_CHOICES
from ..models import WebhookEndpoint, WebhookDelivery


class WebhookEndpointCreateSerializer(serializers.Serializer):
    url = serializers.URLField()
    description = serializers.CharField(max_length=200, required=False, default="")
    subscribed_events = serializers.ListField(
        child=serializers.ChoiceField(choices=[e[0] for e in EVENT_CHOICES]),
        required=False,
        default=list,
    )


class WebhookEndpointSerializer(serializers.ModelSerializer):
    delivery_count = serializers.SerializerMethodField()
    last_delivery_status = serializers.SerializerMethodField()

    class Meta:
        model = WebhookEndpoint
        fields = [
            "id", "url", "description", "subscribed_events",
            "is_active", "delivery_count", "last_delivery_status",
            "created_at",
        ]
        read_only_fields = fields

    def get_delivery_count(self, obj):
        return obj.deliveries.count()

    def get_last_delivery_status(self, obj):
        last = obj.deliveries.order_by("-created_at").first()
        return last.status if last else None


class WebhookEndpointCreatedSerializer(WebhookEndpointSerializer):
    """Includes raw secret — returned once on creation only."""
    raw_secret = serializers.CharField(read_only=True)

    class Meta(WebhookEndpointSerializer.Meta):
        fields = WebhookEndpointSerializer.Meta.fields + ["raw_secret"]


class WebhookDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookDelivery
        fields = [
            "id", "event_type", "status",
            "response_status_code", "response_body",
            "error_message", "attempt_count",
            "next_retry_at", "created_at", "delivered_at",
        ]
        read_only_fields = fields
