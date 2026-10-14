import logging

from retrieval.tenant_stores import get_memory_store
logger = logging.getLogger(__name__)

def search_chat_history(org_id: str, user_id: str, query: str,
                        exclude_thread_id: str | None = None, k: int = 3):
    if not query or not query.strip():
        raise ValueError("query must not be empty")
    filters = [{"org_id": {"$eq": org_id}}, {"user_id": {"$eq": user_id}}]
    if exclude_thread_id:
        filters.append({"source_thread_id": {"$ne": exclude_thread_id}})
    retriever = get_memory_store(org_id).as_retriever(
        search_type="similarity", search_kwargs={"k": k, "filter": {"$and": filters}}
    )
    return retriever.invoke(query)