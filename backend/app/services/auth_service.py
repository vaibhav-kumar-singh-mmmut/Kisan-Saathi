"""
Auth service — OTP request + OTP verify/login logic.

Searches both `farmers` and `officials` tables by phone.
JWT payload includes user_type, role, wing, jurisdiction_type, jurisdiction_id.
"""

import logging
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.farmer import Farmer
from app.models.official import Official
from app.models.jurisdiction import Jurisdiction
from app.utils.otp import generate_otp, verify_otp
from app.utils.jwt_utils import create_access_token
from app.schemas.auth import OTPRequestResponse, TokenResponse, SignupRequest

logger = logging.getLogger(__name__)


def request_otp(phone: str, db: Session) -> OTPRequestResponse:
    """
    Look up phone in officials OR farmers.
    Generate OTP and return it (in dev mode) or log it.
    Raises 404 if phone not found in either table.
    """
    # Check officials first (more common in demo flow)
    official = db.execute(
        select(Official).where(Official.phone == phone)
    ).scalar_one_or_none()
    farmer = None
    if not official:
        farmer = db.execute(
            select(Farmer).where(Farmer.phone == phone)
        ).scalar_one_or_none()

    if not official and not farmer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not registered.",
        )

    code = generate_otp(phone)

    # Log the code server-side (always useful for debugging)
    logger.info("[OTP] %s → %s", phone, code)

    # In dev mode: return the code in the response for easy testing
    dev_code: Optional[str] = code if settings.DEV_RETURN_OTP else None

    return OTPRequestResponse(otp_sent=True, dev_code=dev_code)


def verify_otp_and_login(phone: str, code: str, db: Session) -> TokenResponse:
    """
    Verify OTP. If correct, build and return a JWT token.
    Raises 401 on wrong/expired OTP.
    """
    if not verify_otp(phone, code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP.",
        )

    # Identify the user
    official = db.execute(
        select(Official).where(Official.phone == phone)
    ).scalar_one_or_none()

    if official:
        jurisdiction_name = None
        if official.jurisdiction_id:
            jur = db.execute(select(Jurisdiction).where(Jurisdiction.id == official.jurisdiction_id)).scalar_one_or_none()
            if jur:
                jurisdiction_name = jur.name

        payload = {
            "sub": official.id,
            "user_type": "official",
            "role": str(official.role),  # type: ignore
            "wing": str(official.wing) if official.wing else None,  # type: ignore
            "jurisdiction_type": str(official.jurisdiction_type),  # type: ignore
            "jurisdiction_id": str(official.jurisdiction_id) if official.jurisdiction_id else "",  # type: ignore
            "jurisdiction_name": jurisdiction_name,
            "name": official.name,
            "phone": official.phone,
        }
        return TokenResponse(
            access_token=create_access_token(payload),
            user_type="official",
            role=str(official.role),  # type: ignore
            wing=str(official.wing) if official.wing else None,  # type: ignore
            jurisdiction_type=str(official.jurisdiction_type),  # type: ignore
            jurisdiction_id=str(official.jurisdiction_id) if official.jurisdiction_id else "",  # type: ignore
            jurisdiction_name=jurisdiction_name,
        )

    farmer = db.execute(
        select(Farmer).where(Farmer.phone == phone)
    ).scalar_one_or_none()
    if farmer:
        jurisdiction_name = None
        if farmer.jurisdiction_id:
            jur = db.execute(select(Jurisdiction).where(Jurisdiction.id == farmer.jurisdiction_id)).scalar_one_or_none()
            if jur:
                jurisdiction_name = jur.name

        payload = {
            "sub": farmer.id,
            "user_type": "farmer",
            "role": "Farmer",
            "wing": None,
            "jurisdiction_type": "village",
            "jurisdiction_id": str(farmer.jurisdiction_id) if farmer.jurisdiction_id else "",  # type: ignore
            "jurisdiction_name": jurisdiction_name,
            "name": farmer.name,
            "phone": farmer.phone,
        }
        return TokenResponse(
            access_token=create_access_token(payload),
            user_type="farmer",
            role="Farmer",
            jurisdiction_type="village",
            jurisdiction_id=str(farmer.jurisdiction_id) if farmer.jurisdiction_id else "",  # type: ignore
            jurisdiction_name=jurisdiction_name,
        )

    # Should never reach here — OTP was valid but user disappeared
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="User not found after OTP verification.",
    )


def signup_user(body: SignupRequest, db: Session) -> dict:
    """
    Register a new user (Farmer or Official).
    """
    official = db.execute(select(Official).where(Official.phone == body.phone)).scalar_one_or_none()
    farmer = db.execute(select(Farmer).where(Farmer.phone == body.phone)).scalar_one_or_none()

    if official or farmer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered."
        )

    jurisdiction_id = None
    jurisdiction_type = body.jurisdiction_type or "village"

    # Grab a random jurisdiction of this type for hackathon simplicity
    jur = db.execute(select(Jurisdiction).where(Jurisdiction.jurisdiction_type == jurisdiction_type)).scalars().first()
    if jur:
        jurisdiction_id = jur.id

    if body.user_type == "farmer":
        new_farmer = Farmer(
            name=body.name,
            phone=body.phone,
            jurisdiction_id=jurisdiction_id
        )
        db.add(new_farmer)
    else:
        new_official = Official(
            name=body.name,
            phone=body.phone,
            role=body.role or "Official",
            wing=body.wing or "revenue",
            jurisdiction_type=jurisdiction_type,
            jurisdiction_id=jurisdiction_id
        )
        db.add(new_official)

    db.commit()
    return {"message": "User registered successfully"}
