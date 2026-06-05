from rest_framework import serializers


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
