from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BaseAuthentication

from .models import APIKey


def get_client_ip(request):
    """
    Best-effort client IP. Behind nginx the real address is the first
    entry of X-Forwarded-For; fall back to REMOTE_ADDR for direct calls.
    """
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class APIKeyAuthentication(BaseAuthentication):
    """
    Authenticate via X-API-Key header.

    Clients send:
        X-API-Key: fp_abc123...

    On success returns (user, api_key) — DRF sets request.user
    to the org owner and request.auth to the APIKey instance.
    """

    keyword = "X-API-Key"

    def authenticate(self, request):  # Return None so DRF tries the next authentication class (JWT)
        raw_key = request.META.get("HTTP_X_API_KEY")

        if not raw_key:
            return None

        api_key = APIKey.authenticate(raw_key)

        if api_key is None:
            raise AuthenticationFailed("Invalid or expired API key.")

        if not api_key.is_ip_allowed(get_client_ip(request)):
            raise AuthenticationFailed("This API key is not permitted from your IP address.")

        if not api_key.organization.members.filter(is_active=True).exists():
            raise AuthenticationFailed("Organization has no active members.")

        return api_key.created_by, api_key

    def authenticate_header(self, request):
        return self.keyword
