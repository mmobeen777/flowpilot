from django.db import transaction
from django.utils.text import slugify
from django.contrib.auth import get_user_model

from rest_framework import serializers, exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from ..models import Organization

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Add org slug and role to the JWT payload."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["role"] = user.role

        if user.organization:
            token["org"] = str(user.organization.id)
            token["org_slug"] = user.organization.slug

        return token


class OrganizationSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "member_count", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]

    def get_member_count(self, obj):
        return obj.members.count()


class CreateUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    org_name = serializers.CharField(max_length=150)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")

        return value.lower()

    def validate_org_name(self, value):
        slug = slugify(value)
        if Organization.objects.filter(slug=slug).exists():
            raise serializers.ValidationError("An organization with this name already exists. Ask your organization to add you.")

        return value

    def create(self, validated_data):

        try:
            with transaction.atomic():
                org = Organization.objects.create(name=validated_data["org_name"],
                                                  slug=slugify(validated_data["org_name"]))

                user = User.objects.create_user(
                    email=validated_data["email"],
                    password=validated_data["password"],
                    first_name=validated_data["first_name"],
                    last_name=validated_data["last_name"],
                    organization=org,
                    role=User.Role.OWNER,
                )
                return user
        except Exception as e:
            raise exceptions.ValidationError("Unable to create user at this time.")


class CreateMemberUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    org_id = serializers.PrimaryKeyRelatedField(required=True,
                                                queryset=Organization.objects.filter(is_active=True).all())

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")

        return value.lower()

    def create(self, validated_data):

        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            organization=validated_data["org_id"],
            role=User.Role.MEMBER,
        )
        return user


class ResetPasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")

        user = self.context["request"].user

        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError("Old password is incorrect")

        return attrs


class UserSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role", "organization"]
        read_only_fields = ["id", "role"]
