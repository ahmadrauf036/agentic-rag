import logging

from fastapi import APIRouter, Depends, HTTPException, status

from agent.session_manager import delete_session, get_or_create_graph
from core.auth import AuthenticatedUser, get_current_user
from db.sessions import list_sessions
from db.sessions import get_session as db_get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("")
def get_sessions(user: AuthenticatedUser = Depends(get_current_user)):
    return list_sessions(user.user_id)


@router.get("/{thread_id}/messages")
async def get_session_messages(thread_id: str, user: AuthenticatedUser = Depends(get_current_user)):
    try:
        graph = await get_or_create_graph(thread_id=thread_id, user_id=user.user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")

    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    messages = state.values.get("messages", [])

    result = []
    pending_sources = []

    for m in messages:
        role = getattr(m, "type", None)
        content = getattr(m, "content", None)

        if role == "tool":
            artifact = getattr(m, "artifact", None)
            if artifact:
                pending_sources.extend(artifact)
            continue

        if role == "human" and content:
            result.append({"role": "user", "content": content})
            pending_sources = []  # reset — sources belong to the NEXT assistant message
        elif role == "ai" and content:
            result.append({
                "role": "assistant",
                "content": content,
                "sources": pending_sources if pending_sources else None,
            })
            pending_sources = []

    return result


@router.delete("/{thread_id}")
def remove_session(
    thread_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    deleted = delete_session(thread_id, user.user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {"success": True, "detail": f"Deleted session {thread_id}"}

@router.get("/{thread_id}")
def get_session_info(thread_id: str, user: AuthenticatedUser = Depends(get_current_user)):
    session = db_get_session(thread_id, user.user_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session