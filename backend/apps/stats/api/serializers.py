from django.conf import settings
from rest_framework import serializers

from ..models import Export


class DailyUsageSerializer(serializers.Serializer):
    date = serializers.DateField()
    calls = serializers.IntegerField()


class UsageSummarySerializer(serializers.Serializer):
    today = serializers.IntegerField()
    this_week = serializers.IntegerField()
    this_month = serializers.IntegerField()
    all_time = serializers.IntegerField()


class QuotaTrendPointSerializer(serializers.Serializer):
    date = serializers.CharField()
    calls = serializers.IntegerField()
    limit = serializers.IntegerField(allow_null=True)
    percent = serializers.FloatField(allow_null=True)


class TopAPIKeySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    prefix = serializers.CharField()
    created_by = serializers.EmailField(allow_null=True)
    last_used_at = serializers.CharField(allow_null=True)
    created_at = serializers.CharField()


class PeakDaySerializer(serializers.Serializer):
    date = serializers.CharField()
    calls = serializers.IntegerField()


class MonthlyTotalSerializer(serializers.Serializer):
    month = serializers.CharField()
    label = serializers.CharField()
    calls = serializers.IntegerField()


class ExportRequestSerializer(serializers.Serializer):
    format = serializers.ChoiceField(choices=Export.Format.choices, default="csv")
    date_from = serializers.DateField()
    date_to = serializers.DateField()

    def validate(self, data):
        if data["date_from"] > data["date_to"]:
            raise serializers.ValidationError(
                {"date_from": "date_from must be before date_to."}
            )

        if (data["date_to"] - data["date_from"]).days > 365:
            raise serializers.ValidationError(
                {"date_to": "Export range cannot exceed 365 days."}
            )
        return data


class ExportSerializer(serializers.ModelSerializer):
    requested_by_email = serializers.EmailField(source="requested_by.email", read_only=True, default=None)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Export
        fields = [
            "id", "format", "date_from", "date_to",
            "status", "row_count", "file_name",
            "requested_by_email", "download_url",
            "created_at", "completed_at",
        ]
        read_only_fields = fields

    def get_download_url(self, obj):
        if obj.status != Export.Status.COMPLETE:
            return None

        request = self.context.get("request")
        url = f"{settings.APP_CONTEXT_ROOT}/v1/stats/exports/{obj.id}/download"

        return request.build_absolute_uri(url) if request else url
