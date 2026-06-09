import hashlib, hmac, time,  uuid
from apps.utils.Fields import CharIDField


def build_payload(event_type: str, data: dict, org_id: str) -> dict:
    """
    Standard envelope for every webhook payload.
    Receivers always get the same shape regardless of event.
    """
    return {
        "id": str(CharIDField(prefix='web_end_')),          # unique event ID for deduplication
        "type": event_type,
        "created": int(time.time()),
        "organization_id": org_id,
        "data": data,
    }


def compute_signature(secret: str, timestamp: str, body: str) -> str:
    message = f"{timestamp}.{body}"
    return hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()


def build_headers(secret: str, body: str) -> dict:
    """
    Returns the headers to attach to every webhook POST request.
    Timestamp is included so receivers can reject replayed requests.
    """
    timestamp = str(int(time.time()))
    signature = compute_signature(secret, timestamp, body)
    return {
        "Content-Type": "application/json",
        "X-FlowPilot-Timestamp": timestamp,
        "X-FlowPilot-Signature": f"v1={signature}",
        "X-FlowPilot-Event": "",   # filled in by the delivery task
        "User-Agent": "FlowPilot-Webhooks/1.0",
    }
