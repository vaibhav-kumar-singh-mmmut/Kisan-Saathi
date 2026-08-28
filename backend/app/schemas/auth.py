"""
Pydantic v2 schemas for auth endpoints.

OTPRequest  → POST /auth/otp/request
OTPVerify   → POST /auth/otp/verify
TokenResponse / UserMe → responses
"""
from typing import Optional
from pydantic import BaseModel, Field


class OTPRequest(BaseModel):
    """Body for OTP generation request."""
    phone: str = Field(..., description="Registered phone number (E.164 or local format)")


class OTPVerify(BaseModel):
    """Body for OTP verification + login."""
    phone: str
    code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")


class TokenResponse(BaseModel):
    """Returned on successful OTP verification."""
    access_token: str
    token_type: str = "bearer"
    user_type: str       # "farmer" | "official"
    role: str            # e.g. "Tehsildar", "DM", "Farmer"
    wing: Optional[str] = None   # revenue/development/panchayat/service (officials only)
    jurisdiction_type: str       # district/tehsil/block/village
    jurisdiction_id: str


class UserMe(BaseModel):
    """Current user info returned by GET /auth/me."""
    id: str
    name: str
    phone: str
    user_type: str
    role: str
    wing: Optional[str] = None
    jurisdiction_type: str
    jurisdiction_id: Optional[str] = None


class OTPRequestResponse(BaseModel):
    """Response for POST /auth/otp/request."""
    otp_sent: bool = True
    # Only present when DEV_RETURN_OTP=True (never in production)
    dev_code: Optional[str] = None
    message: str = "OTP sent"
