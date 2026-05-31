from django.contrib.auth import get_user_model

from rest_framework.response import Response
from rest_framework import generics, permissions, status
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.utils.core.Permissions import SameOrganizationPermission
from .serializers import CreateUserSerializer, ResetPasswordSerializer, UserSerializer,\
    CustomTokenObtainPairSerializer

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CreateView(generics.CreateAPIView):
    serializer_class = CreateUserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        data = UserSerializer(user).data

        return Response(data, status=status.HTTP_201_CREATED)


class DetailView(generics.RetrieveAPIView):
    permission_classes = [SameOrganizationPermission]
    serializer_class = UserSerializer
    queryset = User.objects.filter(is_active=True)
    lookup_field = "id"


class PasswordResetView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ResetPasswordSerializer
    http_method_names = ["patch"]

    def perform_update(self, serializer):
        user = self.request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()


