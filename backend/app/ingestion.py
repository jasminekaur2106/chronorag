import hashlib
from datetime import date

from .chunking import chunk_text
from .embeddings import embed_texts


def content_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode("utf-8")).hexdigest()


def add_version(conn, document_id: int, effective_date: date, content: str) -> dict:
    """Store a new version and update chunk validity intervals.

    - Chunks identical to a currently-valid chunk are REUSED (no re-embedding).
    - Chunks that disappeared get valid_to = effective_date (they are "closed").
    - Brand-new chunks are embedded and inserted with valid_from = effective_date.
    """
    latest = conn.execute(
        """SELECT version_number, effective_date FROM document_versions
           WHERE document_id = %s ORDER BY version_number DESC LIMIT 1""",
        (document_id,),
    ).fetchone()

    if latest and effective_date <= latest["effective_date"]:
        raise ValueError(
            f"effective_date must be after the latest version ({latest['effective_date']}). "
            "Versions have to be added in chronological order."
        )

    version_number = latest["version_number"] + 1 if latest else 1
    conn.execute(
        """INSERT INTO document_versions (document_id, version_number, effective_date, content)
           VALUES (%s, %s, %s, %s)""",
        (document_id, version_number, effective_date, content),
    )

    # dict keeps order and removes duplicate paragraphs inside the same version
    new_by_hash = {content_hash(c): c for c in chunk_text(content)}

    current = conn.execute(
        "SELECT id, content_hash FROM chunks WHERE document_id = %s AND valid_to IS NULL",
        (document_id,),
    ).fetchall()
    current_by_hash = {row["content_hash"]: row["id"] for row in current}

    removed_ids = [cid for h, cid in current_by_hash.items() if h not in new_by_hash]
    if removed_ids:
        conn.execute(
            "UPDATE chunks SET valid_to = %s WHERE id = ANY(%s)",
            (effective_date, removed_ids),
        )

    to_add = [(h, text) for h, text in new_by_hash.items() if h not in current_by_hash]
    if to_add:
        vectors = embed_texts([text for _, text in to_add])
        for (h, text), vector in zip(to_add, vectors):
            conn.execute(
                """INSERT INTO chunks (document_id, content, content_hash, embedding, valid_from)
                   VALUES (%s, %s, %s, %s, %s)""",
                (document_id, text, h, vector, effective_date),
            )

    return {
        "version_number": version_number,
        "effective_date": effective_date,
        "chunks_total": len(new_by_hash),
        "chunks_reused": len(new_by_hash) - len(to_add),
        "chunks_added": len(to_add),
        "chunks_closed": len(removed_ids),
    }
