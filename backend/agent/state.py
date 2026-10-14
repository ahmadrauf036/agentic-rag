import os

from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, trim_messages, BaseMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
from typing import Literal
from db.audit import logger
from agent.factory import build_agent
from agent.tools.calculator_tool import calculator_tool
from agent.tools.doc_search_tool import make_doc_search_tool
from agent.tools.memory_search_tool import make_memory_search_tool
from agent.tools.recent_messages_tool import recent_messages
from agent.tools.recent_sessions_tool import make_recent_sessions_tool
from config import SYSTEM_PROMPT
from langchain_core.messages.utils import count_tokens_approximately 
from factory import build_tools, build_agent
from context import TenantContext
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

_pool = AsyncConnectionPool(
    conninfo=DATABASE_URL,
    max_size=10,
    kwargs={"autocommit": True, "prepare_threshold": None},
    open=False,
)

_checkpointer: AsyncPostgresSaver | None = None

OLDER_HISTORY_MAX_TOKENS = 800
CURRENT_TURN_MAX_TOKENS = 3000

async def get_checkpointer() -> AsyncPostgresSaver:
    global _checkpointer
    if _checkpointer is None:
        await _pool.open()
        _checkpointer = AsyncPostgresSaver(_pool)
        await _checkpointer.setup()
    return _checkpointer


def should_continue(state: MessagesState) -> Literal['tool_node', END]:
    last_msg = state["messages"][-1]
    if last_msg.tool_calls:
        return 'tool_node'
    return END

def _split_current_turn(messages: list[BaseMessage]) -> tuple[list[BaseMessage], list[BaseMessage]]:
    """
    Split into (older_history, current_turn). current_turn = everything
    from the most recent HumanMessage onward — the in-progress question
    and its own tool-calling loop, which must stay mostly intact for the
    agent to reason over its own just-made tool calls.
    """
    last_human_idx = None
    for i in range(len(messages) - 1, -1, -1):
        if isinstance(messages[i], HumanMessage):
            last_human_idx = i
            break
    if last_human_idx is None:
        return [], messages
    return messages[:last_human_idx], messages[last_human_idx:]


def _trim_older_history(older: list[BaseMessage]) -> list[BaseMessage]:
    """
    Aggressively compress everything before the current turn. First
    filter down to clean Human/final-AI messages only (dropping
    ToolMessages and tool-call-only AIMessages), THEN trim by token
    budget — this avoids trim_messages failing to find a valid
    start_on="human" boundary amid raw tool-call sequences.
    """
    if not older:
        return older

    clean = [
        m for m in older
        if isinstance(m, HumanMessage)
        or (isinstance(m, AIMessage) and m.content and not getattr(m, "tool_calls", None))
    ]

    if not clean:
        return []

    return trim_messages(
        clean,
        max_tokens=OLDER_HISTORY_MAX_TOKENS,
        token_counter=count_tokens_approximately,
        strategy="last",
        start_on="human",
        include_system=False,
        allow_partial=False,
    )


def _trim_current_turn(current_turn: list[BaseMessage]) -> list[BaseMessage]:
    """
    Lighter trim on the in-progress turn. Only kicks in if this turn has
    genuinely ballooned (many tool calls) — in the normal case this is a
    no-op since the turn is still small.
    """
    if not current_turn:
        return current_turn
    return trim_messages(
        current_turn,
        max_tokens=CURRENT_TURN_MAX_TOKENS,
        token_counter=count_tokens_approximately,
        strategy="last",
        start_on="human",
        include_system=False,
        allow_partial=False,
    )
    
async def build_graph(ctx: TenantContext, selected_files: list[str], page: int | None = None):
    tools = build_tools(ctx, selected_files, page)
    agent = build_agent(tools)
    tool_node = ToolNode(tools)
    

    def call_agent(state: MessagesState) -> dict:
        older, current_turn = _split_current_turn(state["messages"])
        trimmed_older = _trim_older_history(older)
        trimmed_current = _trim_current_turn(current_turn)

        messages = [SystemMessage(content=SYSTEM_PROMPT), *trimmed_older, *trimmed_current]
        response = agent.invoke(messages)

        usage = getattr(response, "usage_metadata", None)
        if usage:
            logger.info(
                "LLM call usage: input=%s output=%s total=%s",
                usage.get("input_tokens"), usage.get("output_tokens"), usage.get("total_tokens"),
            )

        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node('call_agent', call_agent)
    graph.add_node('tool_node', tool_node)
    graph.add_edge(START, 'call_agent')
    graph.add_conditional_edges('call_agent', should_continue, ['tool_node', END])
    graph.add_edge('tool_node', 'call_agent')

    checkpointer = await get_checkpointer()
    return graph.compile(checkpointer=checkpointer)