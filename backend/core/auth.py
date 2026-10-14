import logging
import os

import jwt
from dotenv import load_dotenv
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient

from db.tenancy import get_membership

load_dotenv()
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
_jwk_client = PyJWKClient(JWKS_URL)


class Identity:
    """What the token proves: who you are. Says nothing about your org."""

    def __init__(self, user_id: str, email: str | None, is_platform_admin: bool):
        self.user_id = user_id
        self.email = email
        self.is_platform_admin = is_platform_admin


class AuthenticatedUser:
    """A verified identity plus an active org membership, read from the database."""

    def __init__(self, user_id, email, org_id, org_name, role, position):
        self.user_id = user_id
        self.email = email
        self.org_id = org_id
        self.org_name = org_name
        self.role = role
        self.position = position

    @property
    def is_owner(self) -> bool:
        return self.role == "owner"

    @property
    def is_org_admin(self) -> bool:
        return self.role in ("owner", "org_admin")

    @property
    def is_admin(self) -> bool:  # legacy name still used by existing routes
        return self.is_org_admin


def get_identity(authorization: str | None = Header(default=None)) -> Identity:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        signing_key = _jwk_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token, signing_key.key, algorithms=["ES256", "RS256"], audience="authenticated"
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired")
    except jwt.PyJWTError as error:  # also covers unknown signing keys
        logger.warning("Invalid JWT presented: %s", error)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token payload")

    app_metadata = payload.get("app_metadata") or {}
    return Identity(
        user_id=user_id,
        email=payload.get("email"),
        is_platform_admin=app_metadata.get("role") == "platform_admin",
    )


def get_current_user(identity: Identity = Depends(get_identity)) -> AuthenticatedUser:
    membership = get_membership(identity.user_id)
    if membership is None or membership["member_status"] != "active":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "You are not an active member of any organization."
        )
    if membership["org_status"] != "active":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your organization is suspended.")

    return AuthenticatedUser(
        user_id=identity.user_id,
        email=identity.email,
        org_id=str(membership["org_id"]),
        org_name=membership["org_name"],
        role=membership["role"],
        position=membership["position"],
    )


def require_org_admin(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    if not user.is_org_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return user


def require_owner(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    if not user.is_owner:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Organization owner access required")
    return user


def require_platform_admin(identity: Identity = Depends(get_identity)) -> Identity:
    if not identity.is_platform_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Platform admin access required")
    return identity


# Existing routes import this name; it now means "owner or org admin".
require_admin = require_org_admin