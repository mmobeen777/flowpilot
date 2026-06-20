import logging, resend
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def render_email(template_name: str, context: dict):
    """
    Render an HTML template and generate a plain-text fallback.
    Returns (html, plain_text).
    """
    html = render_to_string(f"notifications/{template_name}.html", context)
    plain_text = strip_tags(html)
    return html, plain_text


def send_email(to: str, subject: str, template_name: str, context: dict):
    """
    Render a template and send via Resend.
    Returns the Resend message ID on success, None on failure.
    Never raises — callers should not crash on email failure.
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set — email not sent to %s", to)
        return None

    try:
        html, plain_text = render_email(template_name, context)

        from_address = (
            f"{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>"
        )

        response = resend.Emails.send({
            "from": from_address,
            "to": [to],
            "subject": subject,
            "html": html,
            "text": plain_text,
        })

        message_id = response.get("id", "")
        logger.info("Email sent to %s — subject: %s — id: %s", to, subject, message_id)
        return message_id

    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
        return None
