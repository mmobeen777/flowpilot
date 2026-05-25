from django.contrib.auth import get_user_model
from rest_framework import permissions


User = get_user_model()


# Allow web browsers to query authenticated endpoints for OPTIONS without passing in authentication headers
class IsAuthenticated(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        if request.method == 'OPTIONS':
            return True
        return super(IsAuthenticated, self).has_permission(request, view)


class IsOwnerPermission(permissions.BasePermission):
    message = "Only owner accounts are able to access this"

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return request.user.role == User.Role.OWNER


class IsAdminPermission(permissions.BasePermission):
    message = "Only admin accounts are able to access this"

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return request.user.role == User.Role.ADMIN


class IsMemberPermission(permissions.BasePermission):
    message = "Only member accounts are able to access this"

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return request.user.role == User.Role.MEMBER


class IsAdminPermissionOrOwnerPermission(permissions.BasePermission):
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
