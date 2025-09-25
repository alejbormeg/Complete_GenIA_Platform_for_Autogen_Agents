"""Service layer wiring the FastAPI endpoints to infrastructure."""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import fitz  # type: ignore
import psycopg2
from openai import OpenAI
from psycopg2.extras import RealDictCursor

from tenacity import after_log, before_log, retry, stop_after_delay, wait_exponential

from langchain_app.orchestration.nl2sql_workflow import NL2SQLResult, NL2SQLWorkflow

# Load .env for local dev; in containers Compose env wins because override=False
from dotenv import load_dotenv

load_dotenv(override=False)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:  # pragma: no cover - optional dependency in some environments
    from pgvector.psycopg2 import register_vector
except Exception as exc:  # pragma: no cover - logged for visibility but not fatal
    register_vector = None
    logger.warning("pgvector adapter not available: %s", exc)


# ---------------------------------------------------------------------------
# PostgreSQL configuration and connection helpers
# ---------------------------------------------------------------------------


@dataclass
class PGConfig:
    host: str
    port: int
    db: str
    user: str
    password: str
    sslmode: Optional[str] = None
    application_name: str = "backend"

    @classmethod
    def from_env(cls) -> "PGConfig":
        return cls(
            host=os.getenv("POSTGRES_HOST", "db"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            db=os.getenv("POSTGRES_DB", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            sslmode=os.getenv("POSTGRES_SSLMODE"),
            application_name=os.getenv("PGAPPNAME", "backend"),
        )

    def dsn(self) -> str:
        parts = [
            f"host={self.host}",
            f"port={self.port}",
            f"dbname={self.db}",
            f"user={self.user}",
            f"password={self.password}",
            f"application_name={self.application_name}",
        ]
        if self.sslmode:
            parts.append(f"sslmode={self.sslmode}")
        return " ".join(parts)


def ensure_pgvector(conn: "psycopg2.extensions.connection") -> None:
    """Ensure the pgvector extension is present and register adapters."""

    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()
    if register_vector:
        register_vector(conn)


@retry(
    stop=stop_after_delay(60),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.INFO),
    reraise=True,
)
def open_pg_connection() -> "psycopg2.extensions.connection":
    """Open a psycopg2 connection with retries until Postgres is ready."""

    cfg = PGConfig.from_env()
    logger.info(
        "Connecting to Postgres at %s:%s db=%s user=%s",
        cfg.host,
        cfg.port,
        cfg.db,
        cfg.user,
    )
    conn = psycopg2.connect(dsn=cfg.dsn(), cursor_factory=RealDictCursor)
    ensure_pgvector(conn)
    return conn


# ---------------------------------------------------------------------------
# Domain services
# ---------------------------------------------------------------------------


class VectorService:
    """Responsible for chunking source text and creating embeddings via OpenAI."""

    def __init__(self, client: Optional[OpenAI] = None) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = client or OpenAI(api_key=api_key) if api_key else OpenAI()

    @staticmethod
    def _chunk_text(text: str, chunk_size: int) -> List[str]:
        words = text.split()
        if not words:
            return []
        size = max(1, chunk_size)
        return [
            " ".join(words[idx : idx + size])
            for idx in range(0, len(words), size)
        ]

    @staticmethod
    def _ensure_dimension(chunk_size: int) -> Optional[int]:
        try:
            if chunk_size <= 0:
                return None
            return int(chunk_size)
        except (TypeError, ValueError):
            return None

    def _embed_chunk(self, *, text: str, model: str, dimensions: Optional[int]) -> List[float]:
        payload = {"model": model, "input": text}
        if dimensions:
            payload["dimensions"] = dimensions
        response = self.client.embeddings.create(**payload)
        return response.data[0].embedding

    async def compute_vectors(self, text: str, chunk_size: int, embedding_model: str) -> List[dict]:
        dimensions = self._ensure_dimension(chunk_size)
        chunks = self._chunk_text(text, max(1, dimensions or chunk_size or 512))
        records = []
        for idx, chunk in enumerate(chunks):
            embedding = await asyncio.to_thread(
                self._embed_chunk,
                text=chunk,
                model=embedding_model,
                dimensions=dimensions,
            )
            records.append({
                "entity_id": idx,
                "embedding": embedding,
                "text": chunk,
            })
        return records

    async def extract_text_from_pdf(self, data: bytes) -> str:
        def _extract() -> str:
            with fitz.open(stream=data, filetype="pdf") as doc:
                segments = [page.get_text("text") for page in doc]
            text = "\n".join(segment.strip() for segment in segments if segment.strip())
            if not text:
                raise ValueError("No extractable text found in PDF")
            return text

        return await asyncio.to_thread(_extract)


class PGVectorService:
    """Utility wrapper over pgvector tables inside PostgreSQL."""

    def __init__(self, conn: "psycopg2.extensions.connection") -> None:
        self.conn = conn

    @staticmethod
    def _table_name(chunk_size: int) -> str:
        dimension = int(chunk_size)
        if dimension <= 0:
            raise ValueError("chunk_size must be positive")
        return f"vector_embeddings_{dimension}"

    def _ensure_table(self, chunk_size: int) -> str:
        table = self._table_name(chunk_size)
        ddl = f"""
        CREATE TABLE IF NOT EXISTS {table} (
            id SERIAL PRIMARY KEY,
            entity_id INTEGER NOT NULL,
            embedding vector({int(chunk_size)}),
            text TEXT,
            database TEXT
        );
        """
        with self.conn.cursor() as cur:
            cur.execute(ddl)
        self.conn.commit()
        return table

    async def ping(self) -> bool:
        def _ping() -> bool:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1;")
                return cur.fetchone() is not None

        return await asyncio.to_thread(_ping)

    async def list_vector_databases(self, chunk_size: int) -> List[str]:
        table = self._ensure_table(chunk_size)

        def _list() -> List[str]:
            with self.conn.cursor() as cur:
                cur.execute(
                    f"SELECT DISTINCT database FROM {table} WHERE database IS NOT NULL ORDER BY database;"
                )
                rows = cur.fetchall()
            return [row["database"] for row in rows if row.get("database")]

        return await asyncio.to_thread(_list)

    async def insert_vectors(
        self,
        chunk_size: int,
        vectors: Iterable[dict],
        database: Optional[str],
    ) -> int:
        table = self._ensure_table(chunk_size)
        db_label = database.strip() if database else None

        def _insert() -> int:
            inserted = 0
            with self.conn.cursor() as cur:
                for record in vectors:
                    cur.execute(
                        f"""
                        INSERT INTO {table} (entity_id, embedding, text, database)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            record["entity_id"],
                            record["embedding"],
                            record["text"],
                            db_label or record.get("database"),
                        ),
                    )
                    inserted += 1
            self.conn.commit()
            return inserted

        return await asyncio.to_thread(_insert)

    async def execute_query(self, database: Optional[str], query: str) -> List[List]:
        statement = query.strip()
        if not statement:
            return []

        def _execute() -> List[List]:
            with self.conn.cursor() as cur:
                if database:
                    cur.execute("SET application_name = %s;", (database,))
                cur.execute(statement)
                if cur.description is None:
                    self.conn.commit()
                    return []
                rows = cur.fetchall()
            return [list(row.values()) for row in rows]

        return await asyncio.to_thread(_execute)


class AgentsChatService:
    """Facade over the LangChain NL→SQL workflow."""

    def __init__(self, workflow: Optional[NL2SQLWorkflow] = None) -> None:
        self._workflow = workflow or NL2SQLWorkflow()

    @staticmethod
    def _render_context(rows: List[Dict[str, Any]]) -> str:
        if not rows:
            return "No supporting context retrieved from the vector store."

        formatted: List[str] = []
        for idx, item in enumerate(rows, start=1):
            text = (item.get("text") or "").strip()
            if len(text) > 400:
                text = text[:400].rstrip() + "…"
            score = item.get("score")
            score_label = f"score={score:.4f}" if isinstance(score, (int, float)) else "score=n/a"
            metadata = item.get("metadata") or {}
            meta_pairs = ", ".join(f"{key}={value}" for key, value in metadata.items()) or "none"
            formatted.append(
                f"{idx}. {score_label} | metadata: {meta_pairs}\n   {text}"
            )
        return "\n".join(formatted)

    @staticmethod
    def _build_messages(result: NL2SQLResult) -> List[dict]:
        context = AgentsChatService._render_context(result.retrieved_context)
        sql_block = result.sql_query.strip() or "No SQL query generated."
        plan = result.plan or "Planner could not create a plan."
        if result.database:
            plan = f"Target database: {result.database}\n\n{plan}"
        messages: List[dict] = [
            {
                "role": "user",
                "name": "user",
                "content": result.question,
            },
            {
                "role": "assistant",
                "name": "planner",
                "content": plan,
            },
            {
                "role": "assistant",
                "name": "retriever",
                "content": context,
            },
            {
                "role": "assistant",
                "name": "sql_agent",
                "content": f"```sql\n{sql_block}\n```",
            },
            {
                "role": "assistant",
                "name": "feedback",
                "content": result.feedback or "No feedback returned.",
            },
        ]
        return messages

    async def call_rag_chat(self, task: str, database: Optional[str]) -> List[dict]:
        result = await self._workflow.arun(task, database=database or None)
        return self._build_messages(result)


# ---------------------------------------------------------------------------
# Service container exposed to the FastAPI app
# ---------------------------------------------------------------------------


@dataclass
class AppServices:
    pg_conn: "psycopg2.extensions.connection"
    vector_service: VectorService
    pgvector_service: PGVectorService
    agents_chat_service: AgentsChatService


def build_services() -> AppServices:
    conn = open_pg_connection()
    vector_service = VectorService()
    pgvector_service = PGVectorService(conn)
    agents_chat_service = AgentsChatService()
    return AppServices(
        pg_conn=conn,
        vector_service=vector_service,
        pgvector_service=pgvector_service,
        agents_chat_service=agents_chat_service,
    )
