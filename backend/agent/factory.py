from langchain_core.runnables import Runnable

from agent.tools.calculator_tool import calculator_tool
from agent.tools.doc_search_tool import make_doc_search_tool
from agent.tools.memory_search_tool import make_memory_search_tool
from agent.tools.recent_sessions_tool import make_recent_sessions_tool
from agent.tools.recent_messages_tool import recent_messages
from core.llm import get_llm


def build_agent(
    selected_files: list[str],
    owner_id: str,
    thread_id: str,
    page: int | None = None,
) -> Runnable:
    doc_search_tool = make_doc_search_tool(
        selected_files=selected_files, page=page
    )
    memory_search_tool = make_memory_search_tool(
        owner_id=owner_id, current_thread_id=thread_id
    )
    recent_sessions_tool = make_recent_sessions_tool(owner_id=owner_id)

    tools = [doc_search_tool, calculator_tool, memory_search_tool, recent_sessions_tool, recent_messages]

    llm = get_llm()
    return llm.bind_tools(tools)