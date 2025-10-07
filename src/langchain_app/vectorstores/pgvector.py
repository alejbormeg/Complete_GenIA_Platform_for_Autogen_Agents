"""Reliable pgvector retrieval for LangChain agents.

This module queries your existing `vector_embeddings_*` tables directly using
`pgvector` operators, so it works with the schema created by your SQL init
scripts (id, entity_id, embedding, text, database).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, List, Optional, Dict, Any

import psycopg2
from psycopg2.extras import RealDictCursor

try:
    # In production, the real adapter is installed; in CI there's a no-op shim in /pgvector
    from pgvector.psycopg2 import register_vector  # type: ignore
except Exception:  # pragma: no cover
    # Fallback to the local shim so imports never crash
    from pgvector import psycopg2 as _pgv  # type: ignore
    register_vector = getattr(_pgv, "register_vector", lambda _conn: None)

from langchain_core.documents import Document

from ..embeddings import get_embeddings
from ..settings import LangChainAppSettings


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    text: str
    score: float
    metadata: Dict[str, Any]


def _connect(settings: LangChainAppSettings) -> "psycopg2.extensions.connection":
    """Open a psycopg2 connection using explicit parameters from settings.

    We intentionally **do not** use the SQLAlchemy-style URI here to avoid
    driver mismatches. This guarantees psycopg2 is used consistently.
    """
    return psycopg2.connect(
        host=settings.pg_host,
        port=settings.pg_port,
        dbname=settings.pg_database,
        user=settings.pg_user,
        password=settings.pg_password,
        cursor_factory=RealDictCursor,
    )


def _ensure_pgvector_adapter(conn) -> None:
    """Register pgvector adapter so Python lists map to the `vector` type."""
    try:
        register_vector(conn)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Could not register pgvector adapter: %s", exc)


def _detect_table_shape(conn, table: str) -> Dict[str, bool]:
    """Detects whether expected columns exist in the target table."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            """,
            (table,),
        )
        cols = {row["column_name"] for row in cur.fetchall()}
    return {
        "has_embedding": "embedding" in cols,
        "has_text": "text" in cols,
        "has_database": "database" in cols,
        "has_entity_id": "entity_id" in cols,
    }


def _vectorize(query: str, settings: LangChainAppSettings) -> List[float]:
    embedder = get_embeddings(settings)
    # embed_query returns a list[float]
    return embedder.embed_query(query)

def _build_select_sql(
    table: str,
    filter_db: Optional[str],
    *,
    limit_k: Optional[int] = None,
) -> str:
    where = "WHERE database = %s" if filter_db else ""
    limit_clause = "" if (limit_k is None or int(limit_k) <= 0) else "LIMIT %s"
    # Usamos una CTE 'q(v)' para referenciar el vector una sola vez
    return f"""
        WITH q AS (SELECT %s::vector AS v)
        SELECT
            id,
            entity_id,
            text,
            database,
            1 - (embedding <=> q.v) AS score
        FROM public.{table}, q
        {where}
        ORDER BY embedding <=> q.v ASC
        {limit_clause}
    """

def retrieve(
    settings: LangChainAppSettings,
    query: str,
    *,
    table: Optional[str] = None,
    database_filter: Optional[str] = None,
    k: Optional[int] = None,
    min_score: float = 0.0,
) -> List[RetrievalResult]:
    table = (table or settings.vector_table).strip()
    if not table:
        # No vector table name available — return no context gracefully
        logger.warning("No vector table configured; continuing without context")
        return []

    # First, check table availability/shape before computing embeddings to avoid
    # unnecessary calls when RAG context isn't possible.
    conn = _connect(settings)
    try:
        _ensure_pgvector_adapter(conn)
        shape = _detect_table_shape(conn, table)
        if not (shape.get("has_embedding") and shape.get("has_text")):
            logger.warning(
                "RAG table '%s' not ready (shape=%s); continuing without context",
                table,
                shape,
            )
            return []

        # Table looks good — proceed to embed the query and retrieve neighbors
        query_vec = _vectorize(query, settings)

        sql = _build_select_sql(table, filter_db=database_filter, limit_k=k)

        # ⚠️ Orden correcto de placeholders:
        # 1) vector (CTE q)  2) (opcional) database_filter  3) (opcional) limit
        params: List[Any] = [query_vec]
        if database_filter:
            params.append(database_filter)
        if k is not None and int(k) > 0:
            params.append(int(k))

        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        results: List[RetrievalResult] = []
        for row in rows:
            score = float(row["score"])
            if score < min_score:
                continue
            results.append(
                RetrievalResult(
                    text=row["text"] or "",
                    score=score,
                    metadata={
                        "id": row.get("id"),
                        "entity_id": row.get("entity_id"),
                        "database": row.get("database"),
                        "table": table,
                        "metric": "cosine",
                        "k": k if (k is not None and int(k) > 0) else "ALL",
                    },
                )
            )
        results.sort(key=lambda r: r.score, reverse=True)
        return results
    finally:
        try:
            conn.close()
        except Exception:
            pass

def as_documents(results: Iterable[RetrievalResult]) -> List[Document]:
    """Convert RetrievalResult list to LangChain Documents with score in metadata."""
    docs: List[Document] = []
    for r in results:
        meta = dict(r.metadata)
        meta["score"] = r.score
        docs.append(Document(page_content=r.text, metadata=meta))
    return docs
