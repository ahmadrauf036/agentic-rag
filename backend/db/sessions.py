"""
Session metadata store (Postgres via Supabase) — separate from LangGraph's
own checkpointer tables (which store message state). This table answers
"what chats exist" and "what were they configured with."
"""

import json
import os
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def _get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db() -> None:
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                thread_id TEXT PRIMARY KEY,
                title TEXT,
                selected_files JSONB NOT NULL,
                page INTEGER,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            )
        """)
        conn.commit()

def create_session(thread_id: str, user_id: str, selected_files: list[str], page: int | None, title: str) -> None:
    now = datetime.now(timezone.utc)
    with _get_connection() as conn:
        conn.execute(
            "INSERT INTO sessions (thread_id, user_id, title, selected_files, page, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (thread_id, user_id, title, json.dumps(selected_files), page, now, now),
        )
        conn.commit()


def get_session(thread_id: str, user_id: str) -> dict | None:
    """Only returns the session if it belongs to this user."""
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE thread_id = %s AND user_id = %s",
            (thread_id, user_id),
        ).fetchone()
        return dict(row) if row else None


def list_sessions(user_id: str) -> list[dict]:
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions WHERE user_id = %s ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_session(thread_id: str, user_id: str) -> bool:
    """Only deletes if it belongs to this user."""
    with _get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM sessions WHERE thread_id = %s AND user_id = %s",
            (thread_id, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    
def touch_session(thread_id: str, user_id: str) -> None:
    """Update the session's updated_at timestamp — only for its owner."""
    now = datetime.now(timezone.utc)
    with _get_connection() as conn:
        conn.execute(
            "UPDATE sessions SET updated_at = %s WHERE thread_id = %s AND user_id = %s",
            (now, thread_id, user_id),
        )
        conn.commit()
def pause_sessions_referencing_file(file_hash: str, reason: str) -> int:
    """
    Pause every session (across ALL users) whose selected_files includes
    file_hash. Documents are now shared, so a single deletion can affect
    many different users' sessions, not just the deleter's own.
    """
    with _get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE sessions
            SET paused_reason = %s
            WHERE selected_files @> %s::jsonb
              AND paused_reason IS NULL
            """,
            (reason, json.dumps([file_hash])),
        )
        conn.commit()
        return cursor.rowcount
    
def delete_chat_history_for_thread(thread_id: str, user_id: str) -> None:
    from retrieval.memory_store import get_memory_store
    memory_store = get_memory_store()
    memory_store._collection.delete(
        where={"$and": [{"source_thread_id": thread_id}, {"owner_id": user_id}]}
    )

def unpause_sessions_referencing_file(file_hash: str) -> int:
    """Unpause every session (across ALL users) referencing this file,
    now that it exists again (re-uploaded by an admin)."""
    with _get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE sessions
            SET paused_reason = NULL
            WHERE selected_files @> %s::jsonb
              AND paused_reason IS NOT NULL
            """,
            (json.dumps([file_hash]),),
        )
        conn.commit()
        return cursor.rowcount

def list_all_sessions() -> list[dict]:
    """Admin-only: list every session across every user."""
    with _get_connection() as conn:
        rows = conn.execute("SELECT * FROM sessions ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]