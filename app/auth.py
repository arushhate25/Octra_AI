import hmac
import os

from dotenv import load_dotenv

load_dotenv(override=True)   # local development: values in .env always win

# Which environment variable holds which key, and who it belongs to.
KEY_SETTINGS = {
    "SUPPORT_AGENT_KEY": ("agent", "support_agent"),
    "PAYMENTS_AGENT_KEY": ("agent", "payments_agent"),
    "REVIEWER_KEY": ("approver", "human_reviewer"),
}


def authenticate(api_key):
    """Returns (role, name), or None if the key is missing or wrong."""
    if not api_key:
        return None
    match = None
    for env_name, identity in KEY_SETTINGS.items():
        stored = os.environ.get(env_name)
        if stored and hmac.compare_digest(stored.encode(), api_key.encode()):
            match = identity
    return match