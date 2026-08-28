"""
Auth endpoints.

POST /api/v1/auth/otp/request  — request an OTP (phone lookup)
POST /api/v1/auth/otp/verify   — verify OTP, get JWT
GET  /api/v1/auth/me           — return current user info from JWT

The `/health` endpoint remains in main.py — open, no auth, unchanged.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import (
    OTPRequest, OTPRequestResponse,
    OTPVerify, TokenResponse,
    UserMe,
)
from app.services.auth_service import request_otp, verify_otp_and_login
from app.utils.jurisdiction_scope import CurrentUser

router = APIRouter()


@router.post(
    "/otp/request",
    response_model=OTPRequestResponse,
    summary="Request OTP",
    description=(
        "Look up phone in officials/farmers tables and generate a 6-digit OTP. "
        "In development mode (`DEV_RETURN_OTP=True`), the code is returned in `dev_code` "
        "for easy testing — this field is `null` in production."
    ),
)
def otp_request(
    body: OTPRequest,
    db: Session = Depends(get_db),
):
    return request_otp(body.phone, db)


@router.post(
    "/otp/verify",
    response_model=TokenResponse,
    summary="Verify OTP and get access token",
)
def otp_verify(
    body: OTPVerify,
    db: Session = Depends(get_db),
):
    return verify_otp_and_login(body.phone, body.code, db)


@router.get(
    "/me",
    response_model=UserMe,
    summary="Get current user info",
    description="Returns the decoded JWT payload as structured user info.",
)
def me(current_user: CurrentUser):
    return UserMe(
        id=current_user["sub"],
        name=current_user.get("name", ""),
        phone=current_user.get("phone", ""),
        user_type=current_user["user_type"],
        role=current_user["role"],
        wing=current_user.get("wing"),
        jurisdiction_type=current_user["jurisdiction_type"],
        jurisdiction_id=current_user.get("jurisdiction_id"),
    )
