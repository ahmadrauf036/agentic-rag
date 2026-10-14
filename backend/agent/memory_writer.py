import logging
import uuid
from datetime import datetime, timezone

from langchain_core.documents import Document

from retrieval.tenant_stores import get_memory_store

logger = logging.getLogger(__name__)


def store_turn(org_id: str, user_id: str, thread_id: str, session_title: str,
               user_message: str, assistant_message: str) -> None:
    """Fire-and-forget: a failure here must never break the chat response."""
    try:
        doc = Document(
            page_content=f"User asked: {user_message}\nAssistant answered: {assistant_message}",
            metadata={
                "org_id": org_id, "user_id": user_id, "source_thread_id": thread_id,
                "session_title": session_title,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        get_memory_store(org_id).add_documents(documents=[doc], ids=[str(uuid.uuid4())])
    except Exception:
        logger.exception("Failed to store conversation turn for thread_id=%s", thread_id)


def delete_thread_memory(org_id: str, user_id: str, thread_id: str) -> None:
    get_memory_store(org_id)._collection.delete(
        where={"$and": [{"source_thread_id": thread_id}, {"user_id": user_id}]}
    )


def delete_user_memory(org_id: str, user_id: str) -> None:
    """For member offboarding (E5)."""
    get_memory_store(org_id)._collection.delete(where={"user_id": user_id})