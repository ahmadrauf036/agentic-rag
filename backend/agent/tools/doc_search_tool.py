import logging

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from retrieval.retriever import search

logger = logging.getLogger(__name__)


class DocSearchInput(BaseModel):
    query: str = Field(..., description="The search query to look up in the documents.")


def _format_results(results) -> str:
    if not results:
        return "No relevant information was found in the selected documents."
    parts = []
    for i, doc in enumerate(results, start=1):
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "unknown")
        parts.append(f"[Result {i}] (source: {source}, page: {page})\n{doc.page_content}")
    return "\n\n".join(parts)


def _extract_sources(results) -> list[dict]:
    """Structured source data, kept separate from the LLM-facing string."""
    sources = []
    for doc in results:
        snippet = doc.page_content[:200]
        sources.append({
            "source": doc.metadata.get("source", "unknown"),
            "page": doc.metadata.get("page"),
            "snippet": snippet,
        })
    return sources


def make_doc_search_tool(org_id: str, selected_files: list[str], page: int | None = None, k: int = 3) -> StructuredTool:
    def _run(query: str):
        try:
            results = search(org_id=org_id, selected_files=selected_files, query=query, page=page, k=k)
            content = _format_results(results)
            artifact = _extract_sources(results)
            return content, artifact
        except Exception as error:
            logger.exception("doc_search tool failed for query=%r", query)
            return f"Document search failed: {error}", []

    return StructuredTool.from_function(
        func=_run,
        name="document_search",
        description=(
            "Search the user's uploaded documents for information relevant "
            "to a query. Use this whenever the user asks a question that "
            "might be answered by content in their uploaded files. Do not "
            "use this for general knowledge questions unrelated to the "
            "user's documents, and do not use it for math or calculations."
        ),
        args_schema=DocSearchInput,
        response_format="content_and_artifact",
    )