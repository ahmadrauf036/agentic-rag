"""
Authentication dependency for FastAPI routes.

Verifies the Supabase-issued JWT sent via an HttpOnly cookie, extracting
the authenticated user's ID. Verification is done locally (cryptographic
signature check against Supabase's JWT secret) — no network call to
Supabase needed per-request.
"""

import os
import logging

import jwt
from dotenv import load_dotenv
from fastapi import Cookie, HTTPException, status, Header, Depends
from jwt import PyJWKClient
load_dotenv()

logger = logging.getLogger(__name__)

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
JWT_ALGORITHM = "HS256"
# Supabase's cookie name for the access token — confirm this matches what
# @supabase/ssr actually sets on the frontend once that's wired up.
ACCESS_TOKEN_COOKIE_NAME = "sb-access-token"

SUPABASE_URL = os.getenv("SUPABASE_URL")
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
_jwk_client = PyJWKClient(JWKS_URL)

class AuthenticatedUser:
    def __init__(self, user_id: str, email: str | None = None, role: str = "user"):
        self.user_id = user_id
        self.email = email
        self.role = role

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
    

def get_current_user(authorization: str | None = Header(default=None)) -> AuthenticatedUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = authorization.removeprefix("Bearer ").strip()

    try:
        signing_key = _jwk_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token, signing_key.key, algorithms=["ES256", "RS256"], audience="authenticated"
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    except jwt.InvalidTokenError as error:
        logger.warning("Invalid JWT presented: %s", error)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    app_metadata = payload.get("app_metadata", {}) or {}
    role = app_metadata.get("role", "user")

    return AuthenticatedUser(user_id=user_id, email=payload.get("email"), role=role)

def get_optional_user(
    sb_access_token: str | None = Cookie(default=None, alias=ACCESS_TOKEN_COOKIE_NAME),
) -> AuthenticatedUser | None:
    """Same as get_current_user, but returns None instead of raising —
    useful for routes that behave differently for logged-in vs anonymous
    users without hard-requiring auth."""
    if not sb_access_token:
        return None
    try:
        return get_current_user(sb_access_token)
    except HTTPException:
        return None
    
def require_admin(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user