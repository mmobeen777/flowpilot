USER_OWNER = 'owner'
USER_ADMIN = 'admin'
USER_MEMBER = 'member'


WEBHOOK_EVENTS = [
    ("usage.quota_warning", "Quota Warning"),       # fired at 80% and 100%
    ("usage.quota_exceeded", "Quota Exceeded"),
    ("key.created", "API Key Created"),
    ("key.rotated", "API Key Rotated"),
    ("key.revoked", "API Key Revoked"),
    ("subscription.upgraded", "Subscription Upgraded"),
    ("subscription.cancelled", "Subscription Cancelled"),
]

EVENT_CHOICES = [(e[0], e[1]) for e in WEBHOOK_EVENTS]


