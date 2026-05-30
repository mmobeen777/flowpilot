from enum import Enum, unique
from rest_framework import status


UNEXPECTED_ERROR = "UNEXPECTED_ERROR"
TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"
INVALID_OPERATION = "INVALID_OPERATION"
NOT_FOUND = "NOT_FOUND"
ACCESS_DENIED = "ACCESS_DENIED"
LOGIN_REQUIRED = "LOGIN_REQUIRED"
PERMISSIONS_DENIED = "You do not have permission"

EXCEPTION_MESSAGES = {
    UNEXPECTED_ERROR: "An unexpected error occurred, please try again later.",
    TOO_MANY_REQUESTS: "Too many requests, please try again later.",
    INVALID_OPERATION: "Invalid operation, please try again later.",
    NOT_FOUND: "Requested resource is not available.",
    ACCESS_DENIED: "You are not authorized to access this resource.",
    LOGIN_REQUIRED: "Login required.",
}


@unique
class FlowPilotError(Enum):
    """
    Predefined flowpilot error response codes with standard error messages.

    Format: (http_status_code, severity, message)
    """

    FP0000 = (
        None,
        "Error",
        EXCEPTION_MESSAGES[UNEXPECTED_ERROR],
    )
    FP0001 = (
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "Error",
        EXCEPTION_MESSAGES[UNEXPECTED_ERROR],
    )
    FP0002 = (
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "Error",
        EXCEPTION_MESSAGES[UNEXPECTED_ERROR],
    )
    FP0003 = (
        status.HTTP_429_TOO_MANY_REQUESTS,
        "Error",
        EXCEPTION_MESSAGES[TOO_MANY_REQUESTS],
    )
    FP0004 = (
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        "Error",
        EXCEPTION_MESSAGES[INVALID_OPERATION],
    )
    FP0005 = (
        status.HTTP_406_NOT_ACCEPTABLE,
        "Error",
        EXCEPTION_MESSAGES[INVALID_OPERATION],
    )
    FP0006 = (
        status.HTTP_405_METHOD_NOT_ALLOWED,
        "Error",
        EXCEPTION_MESSAGES[INVALID_OPERATION],
    )
    FP0007 = (
        status.HTTP_404_NOT_FOUND,
        "Error",
        EXCEPTION_MESSAGES[NOT_FOUND],
    )
    FP0008 = (
        status.HTTP_403_FORBIDDEN,
        "Error",
        EXCEPTION_MESSAGES[ACCESS_DENIED],
    )
    FP0009 = (
        status.HTTP_401_UNAUTHORIZED,
        "Error",
        EXCEPTION_MESSAGES[LOGIN_REQUIRED],
    )
    FP0010 = (
        status.HTTP_400_BAD_REQUEST,
        "Error",
        EXCEPTION_MESSAGES[UNEXPECTED_ERROR],
    )

    def __init__(self, http_status_code, severity, message):
        """Initialize with custom error attributes."""
        self.http_status_code = http_status_code
        self.severity = severity
        self.message = message

    @classmethod
    def get_by_http_status_code(cls, http_status_code):
        """Return flowpilot error by http status code."""
        return next(
            (fp_error for fp_error in FlowPilotError if fp_error.http_status_code == http_status_code), FlowPilotError.FP0000
        )
