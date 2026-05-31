import logging
from django.conf import settings

from apps.utils.core.Counter import get_month_count, increment_usage
from backend.apps.utils.core.ErrorHandling import QuotaExceeded, SubscriptionInactive

logger = logging.getLogger(__name__)

root_path = settings.APP_CONTEXT_ROOT
EXCLUDED_PREFIXES = (
    root_path + "/admin/",
    root_path + "v1/users",
    root_path + "v1/invitation",
    root_path + "v1/key",
    root_path + "v1/analytics"
    "/static/",
)


def _get_subscription(user):
    """
    Safely fetch the org's subscription and plan.
    Returns None if anything in the chain is missing.
    """
    try:
        return user.organization.subscription
    except AttributeError:
        return None


class UsageMeteringMiddleware:
    """
        Increments the Redis usage counter for every authenticated
        API request. Runs after Django's auth middleware so
        request.user is already populated.

        Only meters requests that:
        - Are authenticated (request.user.is_authenticated)
        - Belong to an organization (request.user.organization)
        - Are not in EXCLUDED_PREFIXES
        - Return a non-5xx response
        """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # --- QUOTA CHECK (before the view runs) ---
        block_response = self._check_quota(request)
        if block_response:
            return block_response

        # --- RUN THE VIEW ---
        response = self.get_response(request)

        # --- METER AFTER (only on success) ---
        self._maybe_meter(request, response)

        return response

    # ------------------------------------------------------------------ #
    #  Quota check                                                         #
    # ------------------------------------------------------------------ #

    def _check_quota(self, request):
        """
        Return a 429 JsonResponse if the org is over their monthly limit.
        Return None to allow the request through.
        """
        if not self._should_process(request):
            return None

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None

        subscription = _get_subscription(user)
        if not subscription:
            return None

        # Active subscription check
        if not subscription.is_active:
            raise SubscriptionInactive(
                detail="Your subscription is inactive. Please update your billing.",
            )

        # Unlimited plan — never block
        if subscription.plan.is_unlimited:
            return None

        limit = subscription.plan.monthly_call_limit
        used = get_month_count(str(user.organization_id))

        if used >= limit:
            raise QuotaExceeded(used=used, limit=limit, upgrade_url=root_path + "v1/billing/plans")

        return None

    # ------------------------------------------------------------------ #
    #  Metering                                                            #
    # ------------------------------------------------------------------ #

    def _maybe_meter(self, request, response):
        if not self._should_process(request):
            return
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return
        if not request.user.organization_id:
            return
        if response.status_code >= 500:
            return

        increment_usage(str(request.user.organization_id))

    # ------------------------------------------------------------------ #
    #  Helper                                                              #
    # ------------------------------------------------------------------ #

    def _should_process(self, request) -> bool:
        return not any(
            request.path.startswith(p) for p in EXCLUDED_PREFIXES
        )
