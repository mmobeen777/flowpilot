from django.utils import timezone

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status, exceptions

from ..models import APIKey
from apps.webhooks.api.dispatcher import fire_event
from .serializers import APIKeySerializer, APIKeyCreateSerializer, APIKeyCreatedSerializer, APIKeyUpdateSerializer

from apps.utils.core.Permissions import IsAuthenticated, IsAPIKeyAuthenticated,\
    IsOrgAdminPermissionOrIsOrgOwnerPermission


class APIKeyViewSet(viewsets.ModelViewSet):

    http_method_names = ["get", "post", "patch", "delete"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]

        return [IsAuthenticated(), IsOrgAdminPermissionOrIsOrgOwnerPermission()]

    def get_queryset(self):
        return APIKey.objects.filter(organization=self.request.user.organization,
                                     is_active=True).select_related("created_by")

    def get_serializer_class(self):
        if self.action == "create":
            return APIKeyCreateSerializer

        if self.action in ("update", "partial_update"):
            return APIKeyUpdateSerializer

        return APIKeySerializer

    def create(self, request, *args, **kwargs):
        serializer = APIKeyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        instance, raw_key = APIKey.create_key(organization=request.user.organization, created_by=request.user,
                                              name=serializer.validated_data["name"],
                                              expires_at=serializer.validated_data.get("expires_at"),
                                              allowed_ips=serializer.validated_data.get("allowed_ips"))

        instance.raw_key = raw_key

        return Response(APIKeyCreatedSerializer(instance).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=["is_active"])

        fire_event(
            org=request.user.organization,
            event_type="key.revoked",
            data={"key_id": str(instance.id), "key_name": instance.name, "prefix": instance.prefix},
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    def rotate(self, request, pk=None):
        old_key = self.get_object()
        old_key.is_active = False
        old_key.save(update_fields=["is_active"])

        new_instance, raw_key = APIKey.create_key(
            organization=request.user.organization,
            created_by=request.user,
            name=f"{old_key.name} (rotated {timezone.now().strftime('%Y-%m-%d')})",
            expires_at=old_key.expires_at,
        )
        new_instance.raw_key = raw_key

        fire_event(
            org=request.user.organization,
            event_type="key.rotated",
            data={
                "old_key_id": str(old_key.id),
                "new_key_id": str(new_instance.id),
                "key_name": old_key.name,
            },
        )

        return Response(
            APIKeyCreatedSerializer(new_instance).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="rotate")
    def rotate(self, request, pk=None):
        """
        Revoke the existing key and issue a new one with the same name.
        The old hashed_key is kept in the DB (inactive) for audit purposes.
        """
        old_key = self.get_object()
        old_key.delete()

        new_instance, raw_key = APIKey.create_key(organization=request.user.organization, created_by=request.user,
                                                  name=f"{old_key.name} (rotated {timezone.now().strftime('%Y-%m-%d')})",
                                                  expires_at=old_key.expires_at,
                                                  allowed_ips=old_key.allowed_ips)
        new_instance.raw_key = raw_key

        return Response(APIKeyCreatedSerializer(new_instance).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="verify")
    def verify(self, request):
        """
        Lets an API key client verify their key is valid
        and see which org/key it belongs to.
        Only accessible via API key auth (not JWT).
        """

        if not IsAPIKeyAuthenticated().has_permission(request, self):
            raise exceptions.PermissionDenied("This endpoint requires API key authentication.")

        return Response({
            "key_name": request.auth.name,
            "key_prefix": request.auth.prefix,
            "organization": request.user.organization.name,
            "org_slug": request.user.organization.slug,
        })
