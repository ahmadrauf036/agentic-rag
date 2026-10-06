import logging
import threading

from agent.state import build_graph
from db.sessions import create_session, get_session, touch_session
from db.sessions import delete_session as db_delete_session
from db.sessions import delete_chat_history_for_thread
logger = logging.getLogger(__name__)

_graph_cache: dict[tuple[str, str], object] = {}
_lock = threading.Lock()


def _make_title(message: str) -> str:
    stripped = message.strip()
    return (stripped[:50] + "...") if len(stripped) > 50 else stripped


async def get_or_create_graph(
    thread_id: str,
    user_id: str,
    selected_files: list[str] | None = None,
    page: int | None = None,
    first_message: str | None = None,
):
    cache_key = (thread_id, user_id)

    with _lock:
        if cache_key in _graph_cache:
            touch_session(thread_id, user_id)
            return _graph_cache[cache_key]

        existing = get_session(thread_id, user_id)
        if existing:
            logger.info("Reconstructing graph for thread_id=%s user_id=%s", thread_id, user_id)
            graph = await build_graph(
                selected_files=existing["selected_files"],
                owner_id=user_id,
                thread_id=thread_id,
                page=existing["page"],
            )
            _graph_cache[cache_key] = graph
            touch_session(thread_id, user_id)
            return graph

        if not selected_files:
            raise ValueError(
                "selected_files is required to start a new conversation "
                f"(thread_id={thread_id!r} has no existing session for this user)"
            )

        graph = await build_graph(
            selected_files=selected_files, owner_id=user_id, thread_id=thread_id, page=page
        )
        _graph_cache[cache_key] = graph

        title = _make_title(first_message) if first_message else "New chat"
        create_session(thread_id, user_id, selected_files, page, title=title)

        return graph
    
def delete_session(thread_id: str, user_id: str) -> bool:
    with _lock:
        _graph_cache.pop((thread_id, user_id), None)
        delete_chat_history_for_thread(thread_id, user_id)
        return db_delete_session(thread_id, user_id)