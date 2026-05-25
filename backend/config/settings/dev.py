from .base import *

DEBUG = env.bool('DEBUG', False)
ALLOWED_HOSTS = ["*"]

# Show emails in console during dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
