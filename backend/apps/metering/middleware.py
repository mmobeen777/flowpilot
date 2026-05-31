import logging
from django.conf import settings
from apps.utils.core.Counter import increment_usage

logger = logging.getLogger(__name__)

root_path = settings.APP_CONTEXT_ROOT
EXCLUDED_PREFIXES = (
    root_path + "/admin/",
    root_path + "v1/users",
    root_path + "v1/invitation",
    root_path + "v1/key"
    "/static/",
)


class UsageMeteringMiddleware:
    """
    Increments the Redis usage counter for every authenticated
    API request. Runs after Django's auth middleware so
    request.user is already populated.

    Only meters requests that:
    - Are authenticated (request.user.is_authenticated)
    - Belong to an organisation (request.user.organisation)
    - Are not in EXCLUDED_PREFIXES
    - Return a non-5xx response
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only meter after a successful response
        self.meter_request(request, response)

        return response

    def meter_request(self, request, response):
        # Skip excluded paths
        if any(request.path.startswith(p) for p in EXCLUDED_PREFIXES):
            return

        # Skip unauthenticated requests
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return

        # Skip users without an org (shouldn't happen, but be safe)
        if not request.user.organisation_id:
            return

        # Skip server errors — don't charge for your mistakes
        if response.status_code >= 500:
            return

        increment_usage(str(request.user.organisation_id))
