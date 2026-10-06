"""
Tool for retrieving the last few messages of the CURRENT conversation —
a fallback for short/ambiguous messages (e.g. "explain briefly") where
the trimmed context sent to the LLM isn't enough to resolve the reference.

Uses LangGraph's ToolRuntime to read the graph's own state directly,
rather than needing a separate lookup mechanism.
"""

import logging

from langchain_core.messages import HumanMessage, AIMessage
from langchain.tools import ToolRuntime, tool

logger = logging.getLogger(__name__)


@tool
def recent_messages(runtime: ToolRuntime) -> str:
    """
    Retrieve the last few messages of THIS current conversation. Use this
    when the user's message is short or ambiguous (e.g. "explain briefly",
    "what about that") and you cannot tell what they're referring to from
    the context you can currently see.
    """
    try:
        messages = runtime.state.get("messages", [])
        recent = [m for m in messages if isinstance(m, (HumanMessage, AIMessage)) and m.content]
        recent = recent[-6:]

        if not recent:
            return "No prior messages found in this conversation."

        lines = []
        for m in recent:
            role = "User" if isinstance(m, HumanMessage) else "Assistant"
            lines.append(f"{role}: {m.content}")
        return "\n".join(lines)
    except Exception as error:
        logger.exception("recent_messages tool failed")
        return f"Could not retrieve recent messages: {error}"