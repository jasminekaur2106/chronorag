from contextlib import contextmanager

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from .config import settings

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 produces 384-dimensional vectors

# Core idea of the project: every chunk has a validity interval [valid_from, valid_to).
# valid_to = NULL means "still valid today".
SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS documents (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS document_versions (
        id SERIAL PRIMARY KEY,
        document_id INT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        version_number INT NOT NULL,
        effective_date DATE NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE (document_id, version_number),
        UNIQUE (document_id, effective_date)
    )
    """,
    f"""
    CREATE TABLE IF NOT EXISTS chunks (
        id SERIAL PRIMARY KEY,
        document_id INT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        content TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        embedding vector({EMBEDDING_DIM}) NOT NULL,
        valid_from DATE NOT NULL,
        valid_to DATE
    )
    """,
    "CREATE INDEX IF NOT EXISTS chunks_doc_valid_idx ON chunks (document_id, valid_from, valid_to)",
]


def init_db() -> None:
    # The extension must exist before register_vector() can find the "vector" type.
    with psycopg.connect(settings.database_url) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    with get_conn() as conn:
        for statement in SCHEMA:
            conn.execute(statement)


@contextmanager
def get_conn():
    """Open a connection; commits on success, rolls back on error, always closes."""
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        register_vector(conn)
        yield conn
