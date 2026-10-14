import logging

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from core.resilience import with_chroma_resilience
from retrieval.tenant_stores import get_docs_store

logger = logging.getLogger(__name__)


def _build_where_filter(org_id: str, selected_files: list[str], page: int | None) -> dict:
    # The collection is already per-org; the org_id clause is defense in depth.
    filters = [{"org_id": {"$eq": org_id}}, {"file_hash": {"$in": selected_files}}]
    if page is not None:
        filters.append({"page": {"$eq": page}})
    return {"$and": filters}


@with_chroma_resilience
def _fetch_candidate_pool(org_id: str, where: dict, pool_size: int) -> list[Document]:
    raw = get_docs_store(org_id)._collection.get(
        where=where, include=["documents", "metadatas"], limit=pool_size
    )
    return [Document(page_content=c, metadata=m) for c, m in zip(raw["documents"], raw["metadatas"])]


def _bm25_search(query: str, candidates: list[Document], k: int) -> list[Document]:
    if not candidates:
        return []
    bm25 = BM25Okapi([d.page_content.lower().split() for d in candidates])
    scores = bm25.get_scores(query.lower().split())
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return [doc for doc, score in ranked[:k] if score > 0]


@with_chroma_resilience
def _vector_search(org_id: str, query: str, where: dict, k: int) -> list[Document]:
    retriever = get_docs_store(org_id).as_retriever(
        search_type="similarity", search_kwargs={"k": k, "filter": where}
    )
    return retriever.invoke(query)


def _reciprocal_rank_fusion(bm25_results, vector_results, k: int, rrf_k: int = 60) -> list[Document]:
    scores: dict[str, float] = {}
    by_content: dict[str, Document] = {}
    for results in (bm25_results, vector_results):
        for rank, doc in enumerate(results):
            key = doc.page_content
            scores[key] = scores.get(key, 0) + 1 / (rrf_k + rank + 1)
            by_content[key] = doc
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [by_content[key] for key, _ in ranked[:k]]


def hybrid_search(org_id: str, query: str, selected_files: list[str],
                  page: int | None = None, k: int = 3, candidate_pool_size: int = 50) -> list[Document]:
    if not selected_files:
        raise ValueError("selected_files must contain at least one file_hash")
    if not query or not query.strip():
        raise ValueError("query must not be empty")

    where = _build_where_filter(org_id, selected_files, page)
    candidates = _fetch_candidate_pool(org_id, where, candidate_pool_size)
    bm25_results = _bm25_search(query, candidates, k=k * 2)
    vector_results = _vector_search(org_id, query, where, k=k * 2)
    return _reciprocal_rank_fusion(bm25_results, vector_results, k=k)