from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.tasks import deliver_webhook
from ..models import WebhookEndpoint, WebhookDelivery
from apps.utils.core.Permissions import IsOrgAdminPermission, HasFeature
from .serializers import WebhookEndpointCreateSerializer, WebhookEndpointSerializer, WebhookEndpointCreatedSerializer,\
    WebhookDeliverySerializer



class WebhookEndpointListCreateView(APIView):
    """
    GET  /api/webhooks/endpoints/   → list org's endpoints
    POST /api/webhooks/endpoints/   → register a new endpoint
    Requires can_use_webhooks feature (Starter+).
    """
    permission_classes = [HasFeature("can_use_webhooks")]

    def get(self, request):
        endpoints = WebhookEndpoint.objects.filter(
            organization=request.user.organization
        ).prefetch_related("deliveries")
        return Response(
            WebhookEndpointSerializer(endpoints, many=True).data
        )

    def post(self, request):
        serializer = WebhookEndpointCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        instance, raw_secret = WebhookEndpoint.create_endpoint(
            organization=request.user.organization,
            url=serializer.validated_data["url"],
            description=serializer.validated_data.get("description", ""),
            events=serializer.validated_data.get("subscribed_events", []),
        )
        instance.raw_secret = raw_secret

        return Response(
            WebhookEndpointCreatedSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )


class WebhookEndpointDetailView(APIView):

    permission_classes = [HasFeature("can_use_webhooks")]

    def _get_endpoint(self, request, pk):
        try:
            return WebhookEndpoint.objects.get(
                id=pk,
                organization=request.user.organization,
            )
        except WebhookEndpoint.DoesNotExist:
            return None

    def get(self, request, pk):
        endpoint = self._get_endpoint(request, pk)
        if not endpoint:
            return Response({"detail": "Not found."}, status=404)
        return Response(WebhookEndpointSerializer(endpoint).data)

    def delete(self, request, pk):
        endpoint = self._get_endpoint(request, pk)
        if not endpoint:
            return Response({"detail": "Not found."}, status=404)
        endpoint.is_active = False
        endpoint.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class WebhookDeliveryListView(APIView):

    permission_classes = [HasFeature("can_use_webhooks")]

    def get(self, request, pk):
        try:
            endpoint = WebhookEndpoint.objects.get(
                id=pk,
                organization=request.user.organization,
            )
        except WebhookEndpoint.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        deliveries = endpoint.deliveries.order_by("-created_at")[:50]
        return Response(WebhookDeliverySerializer(deliveries, many=True).data)


class WebhookRedeliverView(APIView):
    permission_classes = [IsOrgAdminPermission, HasFeature("can_use_webhooks")]

    def post(self, request, pk):
        try:
            delivery = WebhookDelivery.objects.select_related(
                "endpoint__organization"
            ).get(
                id=pk,
                endpoint__organization=request.user.organization,
            )
        except WebhookDelivery.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        if delivery.status not in (
            WebhookDelivery.Status.FAILED,
            WebhookDelivery.Status.RETRYING,
        ):
            return Response(
                {"detail": "Only failed or retrying deliveries can be redelivered."},
                status=400,
            )

        delivery.status = WebhookDelivery.Status.PENDING
        delivery.error_message = ""
        delivery.save(update_fields=["status", "error_message"])

        deliver_webhook.delay(str(delivery.id))

        return Response(
            WebhookDeliverySerializer(delivery).data,
            status=status.HTTP_202_ACCEPTED,
        )
