from fastapi import APIRouter, Depends, HTTPException, status

from core.auth import AuthenticatedUser, get_current_user, require_org_admin
from db.audit import log_action
from db.documents import delete_document_row, get_document, list_documents
from db.sessions import list_dependent_sessions, pause_sessions_referencing_file
from retrieval.tenant_stores import get_docs_store

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents_route(user: AuthenticatedUser = Depends(get_current_user)):
    return list_documents(user.org_id)


@router.delete("/{file_hash}")
def delete_document(file_hash: str, user: AuthenticatedUser = Depends(require_org_admin)):
    doc = get_document(user.org_id, file_hash)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")

    # Order matters: vectors first, then the registry row, then pause. A failure
    # midway leaves the document still listed, so the admin can simply retry.
    get_docs_store(user.org_id)._collection.delete(where={"file_hash": file_hash})
    delete_document_row(user.org_id, file_hash)
    paused = pause_sessions_referencing_file(
        org_id=user.org_id, file_hash=file_hash,
        reason=f'"{doc["source"]}" was deleted. This chat is paused and can no longer answer new questions.',
    )
    log_action(actor_id=user.user_id, actor_email=user.email, action="document_delete",
               org_id=user.org_id, target=file_hash,
               metadata={"source": doc["source"], "paused_sessions": paused})
    return {"success": True, "detail": f"Deleted document {file_hash}", "paused_sessions": paused}


@router.get("/{file_hash}/dependents")
def get_document_dependents(file_hash: str, user: AuthenticatedUser = Depends(require_org_admin)):
    return list_dependent_sessions(user.org_id, file_hash)