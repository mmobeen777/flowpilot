from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status, exceptions

from ..models import Plan
from .serializers import PlanSerializer, SubscriptionSerializer, SubscriptionUpgradeSerializer

from apps.utils.core.Counter import get_month_count
from apps.utils.core.Permissions import IsAuthenticated, IsOrgAdminPermission


class PlanListView(generics.ListAPIView):
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]
    queryset = Plan.objects.filter(is_active=True)


class SubscriptionDetailView(generics.RetrieveAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.organisation.subscription


class SubscriptionUpgradeView(APIView):
    permission_classes = [IsOrgAdminPermission]

    def post(self, request):
        serializer = SubscriptionUpgradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_plan = Plan.objects.get(tier=serializer.validated_data["tier"])
        subscription = request.user.organisation.subscription
        old_plan = subscription.plan

        if old_plan == new_plan:
            raise exceptions.ValidationError("You are already on this plan.")

        subscription.plan = new_plan
        subscription.save(update_fields=["plan", "updated_at"])

        return Response(
            SubscriptionSerializer(subscription).data,
            status=status.HTTP_200_OK,
        )
