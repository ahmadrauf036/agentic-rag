from fastapi import APIRouter, Depends
from core.auth import AuthenticatedUser, get_current_user, require_admin
from retrieval.vectorstore import get_vector_store
from db.sessions import pause_sessions_referencing_file
import json
from db.sessions import _get_connection

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents(user: AuthenticatedUser = Depends(get_current_user)):
    """Any authenticated user can list the shared document library."""
    vector_store = get_vector_store()
    all_metadata = vector_store._collection.get(include=["metadatas"])["metadatas"]  # no owner_id filter

    seen = {}
    for meta in all_metadata:
        h = meta["file_hash"]
        if h not in seen:
            seen[h] = {"source": meta["source"], "file_hash": h, "chunk_count": 0}
        seen[h]["chunk_count"] += 1

    return list(seen.values())

from db.audit import log_action

@router.delete("/{file_hash}")
def delete_document(file_hash: str, user: AuthenticatedUser = Depends(require_admin)):
    """Only admins can remove a shared document."""
    vector_store = get_vector_store()

    existing = vector_store._collection.get(
        where={"file_hash": file_hash},
        include=["metadatas"],
        limit=1,
    )
    source_name = existing["metadatas"][0]["source"] if existing["metadatas"] else "a document"

    vector_store._collection.delete(where={"file_hash": file_hash})

    # Pause EVERY session referencing this file, across ALL users —
    # not just the admin's own. See Step 6 for the required fix.
    paused_count = pause_sessions_referencing_file(file_hash=file_hash, reason=(
        f'"{source_name}" was deleted. This chat is paused and can no longer answer new questions.'
    ))
    log_action(
        actor_id=user.user_id,
        actor_email=user.email,
        action="document_delete",
        target=file_hash,
        metadata={"source": source_name, "paused_sessions": paused_count},
    )

    return {
        "success": True,
        "detail": f"Deleted document {file_hash}",
        "paused_sessions": paused_count,
    }
    
# api/routes/documents.py
@router.get("/{file_hash}/dependents")
def get_document_dependents(file_hash: str, admin: AuthenticatedUser = Depends(require_admin)):
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT thread_id, user_id, title FROM sessions WHERE selected_files @> %s::jsonb",
            (json.dumps([file_hash]),),
        ).fetchall()
        return [dict(r) for r in rows]