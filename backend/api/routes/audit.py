# api/routes/audit.py (new file)
from fastapi import APIRouter, Depends
from core.auth import AuthenticatedUser, require_admin
from db.audit import list_audit_log

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("")
def get_audit_log(limit: int = 100, user: AuthenticatedUser = Depends(require_admin)):
    return list_audit_log(limit=limit)