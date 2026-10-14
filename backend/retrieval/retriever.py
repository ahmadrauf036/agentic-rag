import logging

from retrieval.retriever import get_vector_store
from retrieval.hybrid_retriever import hybrid_search

logger = logging.getLogger(__name__)
def build_retriever(selected_files: list[str], page: int | None = None, k: int = 3):
    if not selected_files:
        raise ValueError("selected_files must contain at least one file_hash")

    store = get_vector_store()

    filters = [{"file_hash": {"$in": selected_files}}]
    if page is not None:
        filters.append({"page": {"$eq": page}})

    where = filters[0] if len(filters) == 1 else {"$and": filters}

    return store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k, "filter": where},
    )

def search(org_id: str, selected_files: list[str], query: str, page: int | None = None, k: int = 3):
    if len(selected_files) > 1:
        page = None  # page filtering only applies to single-document selections
    return hybrid_search(org_id=org_id, query=query, selected_files=selected_files, page=page, k=k)