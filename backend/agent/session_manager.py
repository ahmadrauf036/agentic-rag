import logging
import threading

from agent.context import TenantContext
from agent.graph import build_graph  # adjust to your module name (state.py)
from agent.memory_writer import delete_thread_memory
from db.documents import get_missing_hashes
from db.sessions import create_session, get_session, touch_session
from db.sessions import delete_session as db_delete_session

logger = logging.getLogger(__name__)

_graph_cache: dict[tuple[str, str, str], object] = {}
_lock = threading.Lock()


def _make_title(message: str) -> str:
    s = message.strip()
    return (s[:50] + "...") if len(s) > 50 else s


async def get_or_create_graph(thread_id: str, user_id: str, org_id: str,
                              selected_files: list[str] | None = None,
                              page: int | None = None, first_message: str | None = None):
    cache_key = (org_id, user_id, thread_id)
    ctx = TenantContext(org_id=org_id, user_id=user_id, thread_id=thread_id)

    with _lock:
        if cache_key in _graph_cache:
            touch_session(thread_id, user_id)
            return _graph_cache[cache_key]

        existing = get_session(thread_id, user_id)
        if existing:
            if str(existing["org_id"]) != org_id:
                raise ValueError("Session not found")
            graph = await build_graph(ctx, existing["selected_files"], existing["page"])
            _graph_cache[cache_key] = graph
            touch_session(thread_id, user_id)
            return graph

        if not selected_files:
            raise ValueError("selected_files is required to start a new conversation")
        if get_missing_hashes(org_id, selected_files):
            raise ValueError("One or more selected documents do not exist in your organization.")

        graph = await build_graph(ctx, selected_files, page)
        _graph_cache[cache_key] = graph
        create_session(thread_id, user_id, org_id, selected_files, page,
                       title=_make_title(first_message) if first_message else "New chat")
        return graph


def delete_session(thread_id: str, user_id: str, org_id: str) -> bool:
    with _lock:
        _graph_cache.pop((org_id, user_id, thread_id), None)
        delete_thread_memory(org_id, user_id, thread_id)
        return db_delete_session(thread_id, user_id)