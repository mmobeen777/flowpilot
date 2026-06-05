import stripe
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status, exceptions

from ..models import Plan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer, SubscriptionUpgradeSerializer

from apps.stats.api.cache import bust_org_cache
from apps.utils.core.Permissions import IsAuthenticated, IsOrgAdminPermission
from apps.utils.Stripe import update_subscription_item, create_subscription, get_upcoming_invoice


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

        if subscription.plan == new_plan:
            return exceptions.ValidationError("Already on this plan.")

        if not new_plan.stripe_price_id:
            return exceptions.ValidationError("This plan is not available for purchase yet.")

        try:
            if subscription.stripe_subscription_id:
                # Existing Stripe subscription → swap the price
                stripe_sub = update_subscription_item(
                    subscription.stripe_subscription_id,
                    new_plan.stripe_price_id,
                )
            else:
                # No Stripe subscription yet → create one
                stripe_sub = create_subscription(
                    subscription.stripe_customer_id,
                    new_plan.stripe_price_id,
                )
                subscription.stripe_subscription_id = stripe_sub.id

            # Store the subscription item ID for usage reporting
            item_id = stripe_sub["items"]["data"][0]["id"]
            subscription.stripe_subscription_item_id = item_id

        except stripe.StripeError as exc:
            return Response({"detail": str(exc)}, status=402)

        subscription.plan = new_plan
        subscription.status = Subscription.Status.ACTIVE
        subscription.save(update_fields=[
            "plan", "status",
            "stripe_subscription_id",
            "stripe_subscription_item_id",
            "updated_at",
        ])

        bust_org_cache(str(request.user.organization_id))

        return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_200_OK)


class UpcomingInvoiceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscription = request.user.organisation.subscription
        if not subscription.stripe_customer_id:
            return exceptions.ValidationError("No billing account linked.")

        try:
            preview = get_upcoming_invoice(subscription.stripe_customer_id)
        except stripe.StripeError as exc:
            return exceptions.ValidationError(str(exc))

        return Response(preview, status=status.HTTP_200_OK)
