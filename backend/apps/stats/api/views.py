from rest_framework.views import APIView
from rest_framework.response import Response

from .cache import cached_query
from apps.utils.core.Permissions import HasFeature, IsAuthenticated
from .queries import get_daily_usage, get_usage_summary, get_quota_trend, get_top_api_keys, get_peak_usage_day, \
    get_monthly_totals

from .serializers import DailyUsageSerializer, UsageSummarySerializer, QuotaTrendPointSerializer, TopAPIKeySerializer,\
    PeakDaySerializer, MonthlyTotalSerializer


def _get_org(request):
    return request.user.organisation


class UsageSummaryView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = _get_org(request)
        org_id = str(org.id)

        data = cached_query(
            f"analytics:{org_id}:summary",
            get_usage_summary,
            org,
        )
        return Response(UsageSummarySerializer(data).data)


class DailyUsageView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = _get_org(request)
        org_id = str(org.id)

        try:
            days = min(int(request.query_params.get("days", 30)), 90)
        except (ValueError, TypeError):
            days = 30

        data = cached_query(
            f"analytics:{org_id}:daily:{days}",
            get_daily_usage,
            org,
            days=days,
        )
        return Response(DailyUsageSerializer(data, many=True).data)


class QuotaTrendView(APIView):

    permission_classes = [HasFeature("can_use_analytics")]

    def get(self, request):
        org = _get_org(request)
        org_id = str(org.id)

        try:
            days = min(int(request.query_params.get("days", 30)), 90)
        except (ValueError, TypeError):
            days = 30

        data = cached_query(
            f"analytics:{org_id}:quota_trend:{days}",
            get_quota_trend,
            org,
            days=days,
        )
        return Response(QuotaTrendPointSerializer(data, many=True).data)


class TopAPIKeysView(APIView):
    permission_classes = [HasFeature("can_use_analytics")]

    def get(self, request):
        org = _get_org(request)
        org_id = str(org.id)

        data = cached_query(
            f"analytics:{org_id}:top_keys",
            get_top_api_keys,
            org,
        )
        return Response(TopAPIKeySerializer(data, many=True).data)


class PeakUsageView(APIView):
    permission_classes = [HasFeature("can_use_analytics")]

    def get(self, request):
        org = _get_org(request)
        org_id = str(org.id)

        try:
            days = min(int(request.query_params.get("days", 30)), 90)
        except (ValueError, TypeError):
            days = 30

        data = cached_query(
            f"analytics:{org_id}:peak:{days}",
            get_peak_usage_day,
            org,
            days=days,
        )

        if data is None:
            return Response({"detail": "No usage data found."}, status=404)

        return Response(PeakDaySerializer(data).data)


class MonthlyTotalsView(APIView):
    permission_classes = [HasFeature("can_use_analytics")]

    def get(self, request):
        org = _get_org(request)
        org_id = str(org.id)

        try:
            months = min(int(request.query_params.get("months", 6)), 12)
        except (ValueError, TypeError):
            months = 6

        data = cached_query(
            f"analytics:{org_id}:monthly:{months}",
            get_monthly_totals,
            org,
            months=months,
        )
        return Response(MonthlyTotalSerializer(data, many=True).data)
