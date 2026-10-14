from fastapi import APIRouter, Depends

from core.auth import Identity, get_identity
from db.tenancy import get_membership

router = APIRouter(tags=["me"])


@router.get("/me")
def me(identity: Identity = Depends(get_identity)):
    membership = get_membership(identity.user_id)

    if membership is None:
        access = "no_membership"
    elif membership["member_status"] != "active":
        access = "removed"
    elif membership["org_status"] != "active":
        access = "org_suspended"
    else:
        access = "active"

    in_org = access in ("active", "org_suspended")
    return {
        "user_id": identity.user_id,
        "email": identity.email,
        "is_platform_admin": identity.is_platform_admin,
        "access": access,
        "organization": (
            {"id": str(membership["org_id"]), "name": membership["org_name"]} if in_org else None
        ),
        "role": membership["role"] if in_org else None,
        "position": membership["position"] if in_org else None,
    }