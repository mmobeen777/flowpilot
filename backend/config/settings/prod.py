from .base import *

DEBUG = env.bool('DEBUG', False)
ALLOWED_HOSTS = env.str("DJANGO_ALLOWED_HOSTS", "").split(",")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True


# LOGGING
# ------------------------------------------------------------------------------
DEBUG_LOG_FILE_SIZE = env.int("DEBUG_LOG_FILE_SIZE", 15)
DEBUG_LOG_FILE_ROTATIONS = env.int("DEBUG_LOG_FILE_ROTATIONS", 5)

ENABLE_INFO_LOGS = env.bool("ENABLE_INFO_LOGS", False)
INFO_LOG_FILE_SIZE = env.int("INFO_LOG_FILE_SIZE", 15)
INFO_LOG_FILE_ROTATIONS = env.int("INFO_LOG_FILE_ROTATIONS", 5)
ERROR_LOG_FILE_SIZE = env.int("ERROR_LOG_FILE_SIZE", 15)
ERROR_LOG_FILE_ROTATIONS = env.int("ERROR_LOG_FILE_ROTATIONS", 5)
ROTATING_FILE_HANDLER = "logging.handlers.RotatingFileHandler"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "default": {
            "format": "[%(asctime)s] [%(levelname)s] [%(pathname)s:%(lineno)d] [%(process)d:%(thread)d]: [%(message)s]"
        }
    },
    "handlers": {
        "console": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "debug_files": {
            "level": "DEBUG",
            "class": ROTATING_FILE_HANDLER,
            "formatter": "default",
            "filename": LOG_DIRECTORY / "debug.log",
            "maxBytes": DEBUG_LOG_FILE_SIZE * 1024 * 1024,
            "backupCount": DEBUG_LOG_FILE_ROTATIONS,
            "mode": "a",
        },
        "info_files": {
            "level": "INFO",
            "class": ROTATING_FILE_HANDLER,
            "formatter": "default",
            "filename": LOG_DIRECTORY / "info.log",
            "maxBytes": INFO_LOG_FILE_SIZE * 1024 * 1024,
            "backupCount": INFO_LOG_FILE_ROTATIONS,
            "mode": "a",
        },
        "error_files": {
            "level": "WARNING",
            "class": ROTATING_FILE_HANDLER,
            "formatter": "default",
            "filename": LOG_DIRECTORY / "error.log",
            "maxBytes": ERROR_LOG_FILE_SIZE * 1024 * 1024,
            "backupCount": ERROR_LOG_FILE_ROTATIONS,
            "mode": "a",
        },
    },
    "root": {"level": "DEBUG", "handlers": ["console", "error_files"]},
    "loggers": {
        "django": {
            "level": "WARNING",
            "handlers": ["console", "error_files"],
            "propagate": False,
        },
        "django.server": {
            "level": "WARNING",
            "handlers": ["console", "error_files"],
            "propagate": False,
        },
        "django.db.backends": {
            "level": "DEBUG" if ENABLE_SQL_LOGGING else "WARNING",
            "handlers": ["console", "debug_files", "error_files"],
            "propagate": False,
        },
        "django.security.*": {
            "level": "WARNING",
            "handlers": ["console", "error_files"],
            "propagate": False,
        },
        "django.security.csrf": {
            "level": "WARNING",
            "handlers": ["console", "error_files"],
            "propagate": False,
        },
    },
}
