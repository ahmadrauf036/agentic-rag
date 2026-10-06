import logging
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row

from db.sessions import DATABASE_URL

logger = logging.getLogger(__name__)


def _get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def log_usage(user_id: str, thread_id: str | None, input_tokens: int, output_tokens: int, model: str) -> None:
    """Record token usage for one LLM call. Never raises — a logging
    failure must not break the actual chat response."""
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO usage_log (user_id, thread_id, input_tokens, output_tokens, total_tokens, model, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (user_id, thread_id, input_tokens, output_tokens, input_tokens + output_tokens, model, datetime.now(timezone.utc)),
            )
            conn.commit()
    except Exception:
        logger.exception("Failed to log usage for user_id=%s", user_id)


def get_user_usage(user_id: str, since_days: int = 30) -> dict:
    """Aggregate usage for one user over the given window."""
    with _get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                COALESCE(SUM(input_tokens), 0) AS total_input_tokens,
                COALESCE(SUM(output_tokens), 0) AS total_output_tokens,
                COALESCE(SUM(total_tokens), 0) AS total_tokens,
                COUNT(*) AS request_count
            FROM usage_log
            WHERE user_id = %s AND created_at > now() - (%s || ' days')::interval
            """,
            (user_id, since_days),
        ).fetchone()
        return dict(row)


def get_all_usage(since_days: int = 30) -> list[dict]:
    """Admin-only: usage grouped by user, for the admin dashboard."""
    with _get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                user_id,
                COALESCE(SUM(input_tokens), 0) AS total_input_tokens,
                COALESCE(SUM(output_tokens), 0) AS total_output_tokens,
                COALESCE(SUM(total_tokens), 0) AS total_tokens,
                COUNT(*) AS request_count
            FROM usage_log
            WHERE created_at > now() - (%s || ' days')::interval
            GROUP BY user_id
            ORDER BY total_tokens DESC
            """,
            (since_days,),
        ).fetchall()
        return [dict(r) for r in rows]