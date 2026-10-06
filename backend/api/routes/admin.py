import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from retrieval.vectorstore import get_vector_store
from core.auth import AuthenticatedUser, require_admin
from core.admin_client import get_admin_client
from db.audit import log_action
from db.sessions import _get_connection as _sessions_connection, list_all_sessions


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def list_users(admin: AuthenticatedUser = Depends(require_admin)):
    try:
        client = get_admin_client()
        response = client.auth.admin.list_users()
        return [
            {
                "id": u.id,
                "email": u.email,
                "role": (u.app_metadata or {}).get("role", "user"),
                "created_at": str(u.created_at) if u.created_at else None,
                "last_sign_in_at": str(u.last_sign_in_at) if u.last_sign_in_at else None,
            }
            for u in response
        ]
    except Exception as error:
        logger.exception("Failed to list users")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to retrieve user list")
    
# api/routes/admin.py — add below list_users



class RoleUpdateRequest(BaseModel):
    role: str  # "admin" or "user"


@router.post("/users/{user_id}/role")
def set_user_role(
    user_id: str,
    payload: RoleUpdateRequest,
    admin: AuthenticatedUser = Depends(require_admin),
):
    if payload.role not in ("admin", "user"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="role must be 'admin' or 'user'",
        )

    if user_id == admin.user_id and payload.role == "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot demote yourself — ask another admin to do this.",
        )

    try:
        client = get_admin_client()
        client.auth.admin.update_user_by_id(
            user_id, {"app_metadata": {"role": payload.role}}
        )
    except Exception as error:
        logger.exception("Failed to update role for user_id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to update user role",
        )

    log_action(
        actor_id=admin.user_id,
        actor_email=admin.email,
        action="role_change",
        target=user_id,
        metadata={"new_role": payload.role},
    )

    return {"success": True, "user_id": user_id, "new_role": payload.role}

@router.get("/stats")
def get_stats(admin: AuthenticatedUser = Depends(require_admin)):
    try:
        client = get_admin_client()
        users = client.auth.admin.list_users()
    except Exception:
        logger.exception("Failed to fetch user count for stats")
        users = []

    try:
        vector_store = get_vector_store()
        all_docs_meta = vector_store._collection.get(include=["metadatas"])["metadatas"]
        unique_docs = {m["file_hash"] for m in all_docs_meta}
        total_chunks = len(all_docs_meta)
    except Exception:
        logger.exception("Failed to fetch document stats")
        unique_docs = set()
        total_chunks = 0

    try:
        with _sessions_connection() as conn:
            session_count = conn.execute("SELECT COUNT(*) AS count FROM sessions").fetchone()["count"]
            paused_count = conn.execute(
                "SELECT COUNT(*) AS count FROM sessions WHERE paused_reason IS NOT NULL"
            ).fetchone()["count"]
    except Exception:
        logger.exception("Failed to fetch session stats")
        session_count = 0
        paused_count = 0

    return {
        "total_users": len(users),
        "total_admins": sum(1 for u in users if (u.app_metadata or {}).get("role") == "admin"),
        "total_documents": len(unique_docs),
        "total_chunks": total_chunks,
        "total_sessions": session_count,
        "paused_sessions": paused_count,
    }

@router.get("/sessions")
def admin_list_all_sessions(admin: AuthenticatedUser = Depends(require_admin)):
    return list_all_sessions()