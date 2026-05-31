from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Invitation
from .serializers import InvitationCreateSerializer, InvitationAcceptSerializer, InvitationSerializer

from ...user.api.serializers import UserSerializer
from apps.utils.core.Permissions import IsOrgAdminPermissionOrIsOrgOwnerPermission


class InvitationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOrgAdminPermissionOrIsOrgOwnerPermission]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return InvitationCreateSerializer
        return InvitationSerializer

    def get_queryset(self):
        return Invitation.objects.filter(organization=self.request.user.organization).select_related("invited_by")

    def create(self, request, *args, **kwargs):
        serializer = InvitationCreateSerializer(data=request.data, context={"request": request})

        serializer.is_valid(raise_exception=True)
        invitation = serializer.save()

        return Response(
            InvitationSerializer(invitation).data,
            status=status.HTTP_201_CREATED,
        )


class AcceptInvitationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = InvitationAcceptSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class RetrieveInvitationView(generics.RetrieveAPIView):
    permission_classes = [IsOrgAdminPermissionOrIsOrgOwnerPermission]
    serializer_class = InvitationSerializer
    lookup_field = "id"

    def get_queryset(self):
        return Invitation.objects.filter(organization=self.request.user.organization,
                                         is_active=True).select_related("invited_by")
