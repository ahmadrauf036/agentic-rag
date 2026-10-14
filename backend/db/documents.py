import psycopg
from psycopg.rows import dict_row

from db.sessions import DATABASE_URL


def _get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def upsert_document(org_id: str, file_hash: str, source: str, chunk_count: int, uploaded_by: str) -> None:
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO documents (org_id, file_hash, source, chunk_count, uploaded_by)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (org_id, file_hash)
            DO UPDATE SET source = EXCLUDED.source, chunk_count = EXCLUDED.chunk_count
            """,
            (org_id, file_hash, source, chunk_count, uploaded_by),
        )
        conn.commit()


def list_documents(org_id: str) -> list[dict]:
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT source, file_hash, chunk_count FROM documents WHERE org_id = %s ORDER BY created_at DESC",
            (org_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_document(org_id: str, file_hash: str) -> dict | None:
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT source, file_hash, chunk_count FROM documents WHERE org_id = %s AND file_hash = %s",
            (org_id, file_hash),
        ).fetchone()
        return dict(row) if row else None


def delete_document_row(org_id: str, file_hash: str) -> bool:
    with _get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM documents WHERE org_id = %s AND file_hash = %s", (org_id, file_hash)
        )
        conn.commit()
        return cur.rowcount > 0


def get_missing_hashes(org_id: str, hashes: list[str]) -> list[str]:
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT file_hash FROM documents WHERE org_id = %s AND file_hash = ANY(%s)",
            (org_id, hashes),
        ).fetchall()
    found = {r["file_hash"] for r in rows}
    return [h for h in hashes if h not in found]