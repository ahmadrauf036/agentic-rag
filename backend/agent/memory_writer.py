"""
Writes completed conversation turns into the chat_history vector store,
for later semantic recall in *other* sessions. Fire-and-forget — failures
here should never break the actual chat response.
"""

import logging
import uuid
from datetime import datetime, timezone

from langchain_core.documents import Document

from retrieval.memory_store import get_memory_store

logger = logging.getLogger(__name__)


def store_turn(
    thread_id: str,
    owner_id: str,
    session_title: str,
    user_message: str,
    assistant_message: str,
) -> None:
    """Embed and store one completed Q&A turn for future semantic recall."""
    try:
        memory_store = get_memory_store()
        content = f"User asked: {user_message}\nAssistant answered: {assistant_message}"

        doc = Document(
            page_content=content,
            metadata={
                "owner_id": owner_id,
                "source_thread_id": thread_id,
                "session_title": session_title,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        memory_store.add_documents(documents=[doc], ids=[str(uuid.uuid4())])
    except Exception as error:
        # Never let memory-writing failures break the actual chat response.
        logger.exception("Failed to store conversation turn for thread_id=%s", thread_id)