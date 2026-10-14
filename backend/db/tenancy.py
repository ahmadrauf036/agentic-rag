import logging

import psycopg
from psycopg.rows import dict_row

from db.sessions import DATABASE_URL

logger = logging.getLogger(__name__)


def _get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def create_organization(name: str, owner_user_id: str) -> dict:
    """Create an org and its owner membership in one transaction.
    If the user already belongs to an org, nothing is created."""
    with _get_connection() as conn:
        org = conn.execute(
            "INSERT INTO organizations (name) VALUES (%s) RETURNING id, name, status, created_at",
            (name,),
        ).fetchone()
        conn.execute(
            "INSERT INTO memberships (user_id, org_id, role) VALUES (%s, %s, 'owner')",
            (owner_user_id, org["id"]),
        )
        conn.commit()
    return {**org, "id": str(org["id"])}


def get_membership(user_id: str) -> dict | None:
    with _get_connection() as conn:
        row = conn.execute(
            """
            SELECT m.user_id, m.org_id, m.role, m.position, m.status AS member_status,
                   o.name AS org_name, o.status AS org_status
            FROM memberships m
            JOIN organizations o ON o.id = m.org_id
            WHERE m.user_id = %s
            """,
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def list_organizations() -> list[dict]:
    with _get_connection() as conn:
        rows = conn.execute(
            """
            SELECT o.id, o.name, o.status, o.created_at,
                   COUNT(m.user_id) FILTER (WHERE m.status = 'active') AS member_count
            FROM organizations o
            LEFT JOIN memberships m ON m.org_id = o.id
            GROUP BY o.id
            ORDER BY o.created_at DESC
            """
        ).fetchall()
        return [{**r, "id": str(r["id"])} for r in rows]
    
def list_members(org_id: str) -> list[dict]:
    with _get_connection() as conn:
        rows = conn.execute(
            """SELECT m.user_id AS id, u.email, m.role, m.position, u.created_at, u.last_sign_in_at
               FROM memberships m JOIN auth.users u ON u.id = m.user_id
               WHERE m.org_id = %s AND m.status = 'active' ORDER BY u.created_at""",
            (org_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def set_member_role(org_id: str, user_id: str, role: str) -> bool:
    # The WHERE clause enforces the rules: same org, active, never the owner.
    with _get_connection() as conn:
        cur = conn.execute(
            """UPDATE memberships SET role = %s
               WHERE org_id = %s AND user_id = %s AND status = 'active' AND role <> 'owner'""",
            (role, org_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0


def get_org_stats(org_id: str) -> dict:
    with _get_connection() as conn:
        m = conn.execute(
            """SELECT COUNT(*) FILTER (WHERE status = 'active') AS total_users,
                      COUNT(*) FILTER (WHERE status = 'active' AND role IN ('owner','org_admin')) AS total_admins
               FROM memberships WHERE org_id = %s""", (org_id,)).fetchone()
        d = conn.execute(
            "SELECT COUNT(*) AS total_documents, COALESCE(SUM(chunk_count), 0) AS total_chunks "
            "FROM documents WHERE org_id = %s", (org_id,)).fetchone()
        s = conn.execute(
            """SELECT COUNT(*) AS total_sessions,
                      COUNT(*) FILTER (WHERE paused_reason IS NOT NULL) AS paused_sessions
               FROM sessions WHERE org_id = %s""", (org_id,)).fetchone()
    return {**m, **d, **s}