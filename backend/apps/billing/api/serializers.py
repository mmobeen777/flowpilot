from rest_framework import serializers
from ..models import Plan, Subscription


class PlanSerializer(serializers.ModelSerializer):
    is_unlimited = serializers.BooleanField(read_only=True)

    class Meta:
        model = Plan
        fields = [
            "id", "name", "tier",
            "monthly_call_limit", "is_unlimited",
            "max_api_keys", "max_members",
            "can_use_webhooks", "can_use_analytics", "can_export_data",
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id", "plan", "status",
            "current_period_start", "current_period_end",
            "created_at",
        ]
        read_only_fields = fields


class SubscriptionUpgradeSerializer(serializers.Serializer):
    tier = serializers.ChoiceField(choices=Plan.Tier.choices)

    def validate_tier(self, value):
        try:
            Plan.objects.get(tier=value, is_active=True)
        except Plan.DoesNotExist:
            raise serializers.ValidationError(
                f"No active plan found for tier '{value}'."
            )
        return value
    