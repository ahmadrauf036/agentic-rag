from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from core.auth import AuthenticatedUser, require_org_admin, require_owner
from db.audit import log_action
from db.sessions import list_org_sessions
from db.tenancy import get_org_stats, list_members, set_member_role

router = APIRouter(prefix="/admin", tags=["admin"])


class RoleUpdateRequest(BaseModel):
    role: Literal["org_admin", "member"]


@router.get("/users")
def list_users(admin: AuthenticatedUser = Depends(require_org_admin)):
    return list_members(admin.org_id)


@router.post("/users/{user_id}/role")
def set_user_role(user_id: UUID, payload: RoleUpdateRequest,
                  owner: AuthenticatedUser = Depends(require_owner)):
    if str(user_id) == owner.user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot change your own role.")
    if not set_member_role(owner.org_id, str(user_id), payload.role):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found in your organization.")
    log_action(actor_id=owner.user_id, actor_email=owner.email, action="role_change",
               org_id=owner.org_id, target=str(user_id), metadata={"new_role": payload.role})
    return {"success": True, "user_id": str(user_id), "new_role": payload.role}


@router.get("/stats")
def stats(admin: AuthenticatedUser = Depends(require_org_admin)):
    return get_org_stats(admin.org_id)


@router.get("/sessions")
def sessions(admin: AuthenticatedUser = Depends(require_org_admin)):
    return list_org_sessions(admin.org_id)