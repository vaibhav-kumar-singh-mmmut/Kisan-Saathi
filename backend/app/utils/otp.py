"""
OTP utility — 6-digit code, 5-min TTL, in-memory store.

Production swap: replace the _otp_store dict with Redis (SETEX + GET + DEL).
The interface stays identical so auth_service.py doesn't need changes.
"""

import random
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.config import settings

# phone -> {"code": str, "expires_at": datetime}
_otp_store: dict[str, dict] = {}


def generate_otp(phone: str) -> str:
    """Generate a 6-digit OTP, store it with TTL, return the code."""
    code = "".join(random.choices(string.digits, k=6))
    _otp_store[phone] = {
        "code": code,
        "expires_at": datetime.now(timezone.utc)
        + timedelta(seconds=settings.OTP_TTL_SECONDS),
    }
    return code


def verify_otp(phone: str, code: str) -> bool:
    """
    Verify OTP for phone.
    Returns True and deletes the entry on success.
    Returns False if not found, expired, or wrong code.
    """
    entry = _otp_store.get(phone)
    if not entry:
        return False

    # Expired?
    if datetime.now(timezone.utc) > entry["expires_at"]:
        _otp_store.pop(phone, None)
        return False

    # Wrong code?
    if entry["code"] != code:
        return False

    # Success — consume the OTP
    _otp_store.pop(phone, None)
    return True


def get_pending_otp(phone: str) -> Optional[str]:
    """Return the current OTP code for a phone (for dev/test use only)."""
    entry = _otp_store.get(phone)
    if not entry:
        return None
    if datetime.now(timezone.utc) > entry["expires_at"]:
        _otp_store.pop(phone, None)
        return None
    return entry["code"]
