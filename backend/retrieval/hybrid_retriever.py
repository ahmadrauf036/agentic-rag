"""
Hybrid (BM25 + vector) search with Reciprocal Rank Fusion (RRF) combining
the two ranked lists. RRF is a well-established, dependency-free technique
(used in Elasticsearch, Azure AI Search, etc.) that combines rankings from
different retrieval methods without needing an additional ML model —
avoids pulling in sentence-transformers/torch, which conflicted with this
project's existing NumPy/torch versions.
"""

import logging

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
from core.resilience import with_chroma_resilience
from retrieval.vectorstore import get_vector_store

logger = logging.getLogger(__name__)


def _build_where_filter(selected_files: list[str], page: int | None) -> dict:
    filters = [
        {"file_hash": {"$in": selected_files}},
    ]
    if page is not None:
        filters.append({"page": {"$eq": page}})
    return filters[0] if len(filters) == 1 else {"$and": filters}

@with_chroma_resilience
def _fetch_candidate_pool(where: dict, pool_size: int = 50) -> list[Document]:
    """Pull a bounded candidate pool from Chroma matching the filter."""
    vector_store = get_vector_store()
    raw = vector_store._collection.get(
        where=where,
        include=["documents", "metadatas"],
        limit=pool_size,
    )
    return [
        Document(page_content=content, metadata=meta)
        for content, meta in zip(raw["documents"], raw["metadatas"])
    ]


def _bm25_search(query: str, candidates: list[Document], k: int) -> list[Document]:
    if not candidates:
        return []
    tokenized_corpus = [doc.page_content.lower().split() for doc in candidates]
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return [doc for doc, score in ranked[:k] if score > 0]

@with_chroma_resilience
def _vector_search(query: str, where: dict, k: int) -> list[Document]:
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(
        search_type="similarity", search_kwargs={"k": k, "filter": where}
    )
    return retriever.invoke(query)


def _reciprocal_rank_fusion(
    bm25_results: list[Document],
    vector_results: list[Document],
    k: int,
    rrf_k: int = 60,
) -> list[Document]:
    """
    Combine two ranked lists: score = sum of 1/(rrf_k + rank + 1) across
    both lists. A document appearing near the top of either list (or both)
    scores highly; rrf_k=60 is the standard default from the original RRF
    paper, dampening the impact of any single rank position.
    """
    scores: dict[str, float] = {}
    doc_by_content: dict[str, Document] = {}

    for rank, doc in enumerate(bm25_results):
        key = doc.page_content
        scores[key] = scores.get(key, 0) + 1 / (rrf_k + rank + 1)
        doc_by_content[key] = doc

    for rank, doc in enumerate(vector_results):
        key = doc.page_content
        scores[key] = scores.get(key, 0) + 1 / (rrf_k + rank + 1)
        doc_by_content[key] = doc

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [doc_by_content[key] for key, _ in ranked[:k]]


def hybrid_search(
    query: str,
    selected_files: list[str],
    page: int | None = None,
    k: int = 3,
    candidate_pool_size: int = 50,
) -> list[Document]:
    """
    Combine BM25 (keyword) and vector (semantic) search over the user's
    filtered document set, merged via Reciprocal Rank Fusion.
    """
    if not selected_files:
        raise ValueError("selected_files must contain at least one file_hash")
    if not query or not query.strip():
        raise ValueError("query must not be empty")

    where = _build_where_filter(selected_files, page)

    candidates = _fetch_candidate_pool(where, pool_size=candidate_pool_size)
    bm25_results = _bm25_search(query, candidates, k=k * 2)
    vector_results = _vector_search(query, where, k=k * 2)

    final = _reciprocal_rank_fusion(bm25_results, vector_results, k=k)

    logger.info(
        "Hybrid search: %d BM25, %d vector, %d after RRF (query=%r)",
        len(bm25_results), len(vector_results), len(final), query,
    )
    return final