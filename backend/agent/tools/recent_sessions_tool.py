import logging

from langchain_core.tools import StructuredTool
from pydantic import BaseModel
from agent.context import TenantContext
from db.sessions import list_sessions

logger = logging.getLogger(__name__)


class RecentSessionsInput(BaseModel):
    pass  # no arguments needed — always just "list my recent chats"


def make_recent_sessions_tool(ctx: TenantContext) -> StructuredTool:
    def _run() -> str:
        try:
            sessions = list_sessions(ctx.user_id)
            if not sessions:
                return "You have no other chat sessions."
            lines = [
                f"- \"{s['title']}\" (last updated: {s['updated_at']})"
                for s in sessions[:10]
            ]
            return "Your recent chat sessions:\n" + "\n".join(lines)
        except Exception as error:
            logger.exception("recent_sessions tool failed")
            return f"Could not retrieve recent sessions: {error}"

    return StructuredTool.from_function(
        func=_run,
        name="recent_sessions",
        description=(
            "List the user's recent chat sessions by title and recency. "
            "Use this when the user asks about their chat history, recent "
            "conversations, or which chats they've had — NOT for recalling "
            "specific content discussed (use memory_search for that)."
        ),
        args_schema=RecentSessionsInput,
    )