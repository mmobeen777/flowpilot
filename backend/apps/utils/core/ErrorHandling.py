from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from rest_framework_simplejwt.exceptions import InvalidToken
from backend.apps.utils.core.FlowPilotErrors import FlowPilotError


class QuotaExceeded(APIException):
    status_code = 429
    default_code = "quota_exceeded"
    default_detail = "Monthly API quota exceeded."

    def __init__(self, used=None, limit=None, upgrade_url=None):
        self.used = used
        self.limit = limit
        self.upgrade_url = upgrade_url

        detail = {
            "message": (
                f"Monthly limit of {limit:,} calls reached. "
                "Upgrade your plan to continue."
            )
            if limit
            else self.default_detail,
            "used": used,
            "limit": limit,
            "upgrade_url": upgrade_url,
        }

        super().__init__(detail)


class SubscriptionInactive(APIException):
    status_code = 402  # Payment Required
    default_code = "subscription_inactive"
    default_detail = "Your subscription is inactive. Please update your billing."

    def __init__(self, detail=None, subscription_id=None):
        self.subscription_id = subscription_id

        detail = detail or self.default_detail
        super().__init__(detail)


def fp_exception_handler(exc, context):
    """
    Handle error response for all exceptions raised by applications.

    Return fp specific error response based on matching FPError.
    Otherwise return default error response.
    """

    response = exception_handler(exc, context)
    if response is not None:
        fp_error = FlowPilotError.get_by_http_status_code(response.status_code)
        error_response = {
            "error": {
                "code": fp_error.name,
                "severity": fp_error.severity,
                "message": fp_error.message,
                "details": get_exception_details(exc),
            }
        }

        if isinstance(exc, QuotaExceeded):
            response["Retry-After"] = "2592000"  # ~30 days

        response.data = error_response
    return response


def handle_invalid_token_exception(invalid_token_exception):
    """Extract exception message from InvalidToken exception."""
    details = None
    if "messages" in invalid_token_exception.detail:
        details = invalid_token_exception.detail["messages"][0]
    elif "detail" in invalid_token_exception.detail:
        details = invalid_token_exception.detail["detail"]
    else:
        details = invalid_token_exception.detail
    return details


def get_exception_details(exc):
    """Get exception details."""
    details = ""
    if isinstance(exc, Throttled):
        details = "Request is throttled. Please try again later."
    else:
        details = (
            handle_invalid_token_exception(exc) if isinstance(exc, InvalidToken) else getattr(exc, "detail", None)
        )
    return details
