# api/routes/audit.py (new file)
from fastapi import APIRouter, Depends,Query
from db.audit import list_audit_log
from core.auth import require_org_admin
from db.usage import get_all_usage


router = APIRouter(prefix="/audit", tags=["audit"])

# audit.py
@router.get("")
def get_audit_log(limit: int = Query(100, ge=1, le=500), admin=Depends(require_org_admin)):
    return list_audit_log(org_id=admin.org_id, limit=limit)

# usage.py: /usage stays per-user; /usage/all is now org-scoped
@router.get("/all")
def all_usage(days: int = 30, admin=Depends(require_org_admin)):
    return get_all_usage(org_id=admin.org_id, since_days=days)