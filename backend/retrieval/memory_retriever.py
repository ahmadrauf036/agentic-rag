import logging

from retrieval.memory_store import get_memory_store

logger = logging.getLogger(__name__)


def search_chat_history(query: str, owner_id: str, exclude_thread_id: str | None = None, k: int = 3):
    """
    Semantic search over past conversation turns, scoped to owner_id.
    Optionally excludes the current thread_id so a session doesn't
    "recall" itself mid-conversation.
    """
    if not query or not query.strip():
        raise ValueError("query must not be empty")

    memory_store = get_memory_store()

    filters = [{"owner_id": {"$eq": owner_id}}]
    if exclude_thread_id:
        filters.append({"source_thread_id": {"$ne": exclude_thread_id}})

    where = filters[0] if len(filters) == 1 else {"$and": filters}

    retriever = memory_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k, "filter": where},
    )
    results = retriever.invoke(query)
    logger.info("Retrieved %d chat_history results for query=%r (owner=%s)", len(results), query, owner_id)
    return results