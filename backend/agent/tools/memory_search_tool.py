import logging

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from agent.context import TenantContext

from retrieval.memory_retriever import search_chat_history

logger = logging.getLogger(__name__)


class MemorySearchInput(BaseModel):
    query: str = Field(..., description="What to search for in past conversations.")


def _format_results(results) -> str:
    if not results:
        return "No relevant past conversations were found."
    parts = []
    for i, doc in enumerate(results, start=1):
        title = doc.metadata.get("session_title", "Untitled chat")
        parts.append(f"[Past conversation {i}: \"{title}\"]\n{doc.page_content}")
    return "\n\n".join(parts)


def make_memory_search_tool(ctx: TenantContext) -> StructuredTool:
    def _run(query: str) -> str:
        try:
            results = search_chat_history(org_id=ctx.org_id, user_id=ctx.user_id,
                                      query=query, exclude_thread_id=ctx.thread_id)
            return _format_results(results)
        except Exception as error:
            logger.exception("memory_search tool failed for query=%r", query)
            return f"Memory search failed: {error}"

    return StructuredTool.from_function(
        func=_run,
        name="memory_search",
        description=(
            "Search the user's past conversations (from other chat sessions) "
            "for relevant context. Use this when the user references something "
            "discussed previously, asks 'what did we talk about before' on a "
            "topic, or when past context would help answer their question. "
            "Do NOT use this for 'what was my previous message/question' — "
            "that refers to THIS conversation, which you already have in "
            "your current context. Do not use this for document content — "
            "use document_search for that instead."
        ),
        args_schema=MemorySearchInput,
    )