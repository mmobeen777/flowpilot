from django.contrib.auth import get_user_model
from rest_framework import permissions


User = get_user_model()


class IsAPIKeyAuthenticated(permissions.BasePermission):
    """
    Passes only when the request was authenticated via API key,
    not JWT. Use on endpoints that should only be hit by API clients.
    """

    def has_permission(self, request, view):

        if request.user.is_anonymous:
            return False
        return isinstance(request.auth, __import__("apps.apikeys.models", fromlist=["APIKey"]).APIKey)


# Allow web browsers to query authenticated endpoints for OPTIONS without passing in authentication headers
class IsAuthenticated(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        if request.method == 'OPTIONS':
            return True
        return super(IsAuthenticated, self).has_permission(request, view)


class IsOrgOwnerPermission(permissions.BasePermission):
    message = "Only owner accounts are able to access this"

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return request.user.role == User.Role.OWNER


class IsOrgAdminPermission(permissions.BasePermission):
    message = "Only admin accounts are able to access this"

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        print(request.user.role)
        return request.user.role == User.Role.ADMIN


class IsOrgMemberPermission(permissions.BasePermission):
    message = "Only member accounts are able to access this"

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return request.user.role == User.Role.MEMBER


class IsOrgAdminPermissionOrIsOrgOwnerPermission(permissions.BasePermission):
    message = "Only {} and {} accounts are able to access this".format(User.Role.OWNER,
                                                                       User.Role.ADMIN)

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return request.user.role == User.Role.ADMIN or request.user.role == User.Role.OWNER


class SameOrganizationPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_anonymous:
            return False
        if request.user.role == User.Role.ADMIN:
            return True
        return request.user.role == User.Role.OWNER and obj.organization == request.user.organization


class HasFeature(permissions.BasePermission):
    """
    Usage:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, HasFeature("can_use_webhooks")]
    """

    def __init__(self, feature: str):
        self.feature = feature

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        try:
            subscription = request.user.organization.subscription
        except AttributeError:
            return False

        if not subscription.is_active:
            return False

        return subscription.has_feature(self.feature)

    def message(self):
        return (
            f"Your current plan does not include this feature. "
            f"Upgrade to access it."
        )
    