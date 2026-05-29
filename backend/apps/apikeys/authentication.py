from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BaseAuthentication

from .models import APIKey


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

        if not api_key.organization.members.filter(is_active=True).exists():
            raise AuthenticationFailed("Organization has no active members.")

        return api_key.created_by, api_key

    def authenticate_header(self, request):
        return self.keyword
