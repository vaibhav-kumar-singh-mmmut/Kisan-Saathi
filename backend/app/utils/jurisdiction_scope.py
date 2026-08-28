"""
FastAPI dependency: get_current_user

Extracts the Bearer JWT from the Authorization header,
decodes it, and returns the payload dict as a typed object.

Used by all protected routes:
  current_user: Annotated[dict, Depends(get_current_user)]
"""
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.utils.jwt_utils import decode_access_token

# tokenUrl is the endpoint clients use to get a token.
# We use our own OTP flow, but this populates the Swagger UI "Authorize" button.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/otp/verify")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict[str, Any]:
    """
    FastAPI dependency — returns the decoded JWT payload.
    Raises HTTP 401 if token is missing, expired, or invalid.
    """
    return decode_access_token(token)


# Convenience type alias used in route signatures
CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
