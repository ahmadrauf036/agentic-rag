import json
import logging
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row

from db.sessions import DATABASE_URL  # reuse existing connection config

logger = logging.getLogger(__name__)


def _get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def log_action(actor_id: str, actor_email: str | None, action: str, org_id: str, target: str | None = None, metadata: dict | None = None) -> None:
    """
    Record an auditable action. Never raises — logging failures must not
    break the actual operation being audited.
    """
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_log (actor_id, actor_email, action, org_id, target, metadata, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (actor_id, actor_email, action, org_id, target, json.dumps(metadata or {}), datetime.now(timezone.utc)),
            )
            conn.commit()
    except Exception as error:
        logger.exception("Failed to write audit log entry: action=%s actor=%s", action, actor_id)


def list_audit_log( org_id:str, limit: int = 100) -> list[dict]:
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT %s AND org_id = %s", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]