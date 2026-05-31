from datetime import timedelta
from django.utils import timezone
from rest_framework import exceptions
from rest_framework.views import APIView
from rest_framework.response import Response

from ..models import UsageRecord
from apps.utils.core.Permissions import IsAuthenticated
from apps.utils.core.Counter import get_month_count, get_day_count


class UsageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.user.organization
        if not org:
            raise exceptions.ValidationError("User has no organization.")

        org_id = str(org.id)
        now = timezone.now()
        today = now.date()

        today_live = get_day_count(org_id)
        month_live = get_month_count(org_id)

        # Historical daily breakdown from Postgres (flushed records)
        thirty_days_ago = today - timedelta(days=30)
        records = UsageRecord.objects.filter(organization=org,date__gte=thirty_days_ago).order_by("date")

        daily = {r.date.isoformat(): r.call_count for r in records}

        # Merge today's live Redis count into the breakdown
        daily[today.isoformat()] = today_live

        return Response({
            "today": today_live,
            "this_month": month_live,
            "daily_breakdown": daily,
        })


class QuotaView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.user.organization
        if not org:
            raise exceptions.ValidationError("User has no organization.")

        month_used = get_month_count(str(org.id))

        plan_limit = getattr(getattr(org, "subscription", None), "plan", None)

        limit = plan_limit.monthly_call_limit if plan_limit else None

        return Response({
            "used": month_used,
            "limit": limit,
            "unlimited": limit is None,
            "percent": round((month_used / limit) * 100, 1) if limit else None,
        })