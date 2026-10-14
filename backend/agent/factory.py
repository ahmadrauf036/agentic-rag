from agent.context import TenantContext
from agent.tools.calculator_tool import calculator_tool
from agent.tools.doc_search_tool import make_doc_search_tool
from agent.tools.memory_search_tool import make_memory_search_tool
from agent.tools.recent_messages_tool import recent_messages
from agent.tools.recent_sessions_tool import make_recent_sessions_tool
from core.llm import get_llm


def build_tools(ctx: TenantContext, selected_files: list[str], page: int | None = None) -> list:
    return [
        make_doc_search_tool(org_id=ctx.org_id, selected_files=selected_files, page=page),
        calculator_tool,
        make_memory_search_tool(ctx),
        make_recent_sessions_tool(ctx),
        recent_messages,
    ]


def build_agent(tools: list):
    return get_llm().bind_tools(tools)