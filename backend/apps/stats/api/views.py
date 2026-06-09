from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from ..models import Export
from .cache import cached_query
from apps.tasks import generate_export
from apps.utils.core.Permissions import HasFeature, IsAuthenticated
from .queries import get_daily_usage, get_usage_summary, get_quota_trend, get_top_api_keys, get_peak_usage_day, \
    get_monthly_totals

from .serializers import DailyUsageSerializer, UsageSummarySerializer, QuotaTrendPointSerializer, TopAPIKeySerializer,\
    PeakDaySerializer, MonthlyTotalSerializer, ExportSerializer, ExportRequestSerializer


def _get_org(request):
    return request.user.organization


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


class ExportListCreateView(APIView):

    permission_classes = [HasFeature("can_export_data")]

    def get(self, request):
        exports = Export.objects.filter(
            organization=request.user.organization
        ).exclude(status=Export.Status.FAILED)

        serializer = ExportSerializer(
            exports, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = ExportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        export = Export.objects.create(
            organization=request.user.organization,
            requested_by=request.user,
            format=serializer.validated_data["format"],
            date_from=serializer.validated_data["date_from"],
            date_to=serializer.validated_data["date_to"],
        )

        generate_export.delay(str(export.id))

        return Response(
            ExportSerializer(export, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )


class ExportDetailView(APIView):
    permission_classes = [HasFeature("can_export_data")]

    def get(self, request, pk):
        try:
            export = Export.objects.get(
                id=pk,
                organization=request.user.organization,
            )
        except Export.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        return Response(
            ExportSerializer(export, context={"request": request}).data
        )


class ExportDownloadView(APIView):
    permission_classes = [HasFeature("can_export_data")]

    def get(self, request, pk):
        try:
            export = Export.objects.get(
                id=pk,
                organization=request.user.organization,
            )
        except Export.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        if export.status != Export.Status.COMPLETE:
            return Response(
                {
                    "detail": "Export is not ready yet.",
                    "status": export.status,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        content_types = {
            Export.Format.CSV: "text/csv",
            Export.Format.JSON: "application/json",
        }

        response = HttpResponse(
            bytes(export.file_content),
            content_type=content_types.get(export.format, "application/octet-stream"),
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{export.file_name}"'
        )
        response["Content-Length"] = len(export.file_content)
        return response
