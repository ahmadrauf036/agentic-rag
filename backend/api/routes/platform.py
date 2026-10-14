from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.auth import Identity, require_platform_admin
from db.audit import log_action
from db.tenancy import create_organization, list_organizations

router = APIRouter(prefix="/platform", tags=["platform"])


class CreateOrgRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    owner_user_id: UUID  # E3 replaces this with an owner email invite


@router.post("/organizations", status_code=status.HTTP_201_CREATED)
def create_org(payload: CreateOrgRequest, admin: Identity = Depends(require_platform_admin)):
    try:
        org = create_organization(payload.name.strip(), str(payload.owner_user_id))
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status.HTTP_409_CONFLICT, "That user already belongs to an organization.")

    log_action(
        actor_id=admin.user_id, actor_email=admin.email, action="org_create",
        target=org["id"], metadata={"name": org["name"], "owner_user_id": str(payload.owner_user_id)},
    )
    return org


@router.get("/organizations")
def get_organizations(admin: Identity = Depends(require_platform_admin)):
    return list_organizations()