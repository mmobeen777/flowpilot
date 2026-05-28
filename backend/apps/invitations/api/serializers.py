from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework import serializers
from ..models import Invitation
from ...user.api.serializers import UserSerializer

User = get_user_model()


class InvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=["admin", "member"], default="member")

    def validate_email(self, value):
        email = value.lower()
        org = self.context["request"].user.organization

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("This user is already in a organization.")

        if Invitation.objects.filter(email=email, organization=org, status="pending").exists():
            raise serializers.ValidationError("A pending invitation already exists for this email.")

        return email

    def create(self, validated_data):
        user = self.context["request"].user

        invitation = Invitation.objects.create(
            organization=user.organization,
            invited_by=user,
            email=validated_data["email"],
            role=validated_data["role"],
            expires_at=timezone.now() + timedelta(days=7),
        )
        return invitation


class InvitationAcceptSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    def validate_token(self, value):
        try:
            invitation = Invitation.objects.select_related("organization").get(
                token=value, status=Invitation.Status.PENDING
            )
        except Invitation.DoesNotExist:
            raise serializers.ValidationError("Invalid or already used invitation token.")

        if invitation.expires_at < timezone.now():
            invitation.status = Invitation.Status.EXPIRED
            invitation.save(update_fields=["status"])
            raise serializers.ValidationError("This invitation has expired.")

        self.context["invitation"] = invitation

        return value

    def create(self, validated_data):
        invitation = self.context["invitation"]

        user = User.objects.create_user(
            email=invitation.email,
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            organization=invitation.organization,
            role=invitation.role,
        )
        invitation.status = Invitation.Status.ACCEPTED
        invitation.save(update_fields=["status"])

        return user


class InvitationSerializer(serializers.ModelSerializer):
    invited_by = UserSerializer(read_only=True)

    class Meta:
        model = Invitation
        fields = ["id", "email", "role", "status", "invited_by", "created_at", "expires_at"]
        read_only_fields = fields
