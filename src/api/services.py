"""Service layer wiring the FastAPI endpoints to infrastructure."""

from __future__ import annotations

import asyncio
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set

import fitz  # type: ignore
import psycopg2
from psycopg2 import sql
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
    def _ensure_dimension(dimensions: Optional[int]) -> Optional[int]:
        try:
            if dimensions is None:
                return None
            value = int(dimensions)
            if value <= 0:
                return None
            return value
        except (TypeError, ValueError):
            return None

    def _embed_chunk(self, *, text: str, model: str, dimensions: Optional[int]) -> List[float]:
        payload = {"model": model, "input": text}
        if dimensions:
            payload["dimensions"] = dimensions
        response = self.client.embeddings.create(**payload)
        return response.data[0].embedding

    async def compute_vectors(
        self,
        text: str,
        chunk_size: int,
        embedding_model: str,
        *,
        dimensions: Optional[int] = None,
    ) -> List[dict]:
        embed_dimensions = self._ensure_dimension(dimensions if dimensions is not None else chunk_size)
        chunk_words = max(1, chunk_size or embed_dimensions or 512)
        chunks = self._chunk_text(text, chunk_words)
        records = []
        for idx, chunk in enumerate(chunks):
            embedding = await asyncio.to_thread(
                self._embed_chunk,
                text=chunk,
                model=embedding_model,
                dimensions=embed_dimensions,
            )
            if embed_dimensions and len(embedding) != embed_dimensions:
                raise ValueError(
                    f"Embedding response dimension mismatch: requested {embed_dimensions}, received {len(embedding)}"
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

    IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    TABLE_DIMENSION_PATTERN = re.compile(r"_(\d+)$")

    def __init__(self, conn: "psycopg2.extensions.connection") -> None:
        self.conn = conn
        try:
            self.database_name = conn.get_dsn_parameters().get("dbname")
        except Exception:  # pragma: no cover - defensive fallback
            self.database_name = None

    def _normalize_table(self, table: str) -> str:
        name = (table or "").strip()
        if not name:
            raise ValueError("Table name must not be empty")
        if not self.IDENTIFIER_PATTERN.fullmatch(name):
            raise ValueError(f"Invalid table name '{table}'")
        return name

    def _table_exists_sync(self, table: str) -> bool:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = %s
                ) AS present;
                """,
                (table,),
            )
            row = cur.fetchone()
        return bool(row and row.get("present"))

    def _infer_dimension_from_table(self, table: str) -> Optional[int]:
        match = self.TABLE_DIMENSION_PATTERN.search(table)
        if not match:
            return None
        try:
            return int(match.group(1))
        except (TypeError, ValueError):  # pragma: no cover - defensive
            return None

    def _resolve_dimension(self, table: str, dimension: Optional[int]) -> int:
        inferred = self._infer_dimension_from_table(table)
        candidate = inferred if inferred is not None else dimension
        if candidate is None:
            raise ValueError(
                f"Unable to determine embedding dimension for table '{table}'. Provide a positive dimension explicitly or ensure the table name ends with an integer suffix."
            )
        try:
            value = int(candidate)
        except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
            raise ValueError(f"Embedding dimension must be an integer for table '{table}'") from exc
        if value <= 0:
            raise ValueError("Embedding dimension must be a positive integer")
        return value

    def _ensure_table_exists(self, table: str) -> str:
        name = self._normalize_table(table)
        if not self._table_exists_sync(name):
            raise ValueError(f"Table '{name}' does not exist in database '{self.database_name}'")
        return name

    def _table_columns_sync(self, table: str) -> List[str]:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position;
                """,
                (table,),
            )
            rows = cur.fetchall()
        return [row["column_name"] for row in rows]

    def _table_vector_dimension_sync(self, table: str) -> Optional[int]:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT CASE WHEN a.atttypmod > 0 THEN a.atttypmod ELSE NULL END AS dimension
                FROM pg_catalog.pg_attribute a
                WHERE a.attrelid = %s::regclass
                AND a.attname = 'embedding'
                AND a.attnum > 0
                AND NOT a.attisdropped;
                """,
                (table,),
            )
            row = cur.fetchone()
        dimension = row.get("dimension") if row else None
        return int(dimension) if dimension is not None else None


    def _verify_database(self, database: Optional[str]) -> None:
        if not database:
            return
        if self.database_name and database != self.database_name:
            raise ValueError(
                f"Connected to database '{self.database_name}' but '{database}' was requested"
            )

    def _create_table_schema(self, name: str, dimension: int) -> None:
        dimension_literal = sql.SQL(str(int(dimension)))
        ddl = sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS {table} (
                id SERIAL PRIMARY KEY,
                entity_id INTEGER NOT NULL,
                embedding vector({dimension}),
                text TEXT,
                database TEXT
            );
            """
        ).format(table=sql.Identifier(name), dimension=dimension_literal)
        with self.conn.cursor() as cur:
            cur.execute(ddl)
        self.conn.commit()

    def _ensure_embedding_column(self, name: str, dimension: int) -> None:
        columns = set(self._table_columns_sync(name))
        dimension_literal = sql.SQL(str(int(dimension)))
        if "embedding" not in columns:
            with self.conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        "ALTER TABLE {table} ADD COLUMN embedding vector({dimension});"
                    ).format(table=sql.Identifier(name), dimension=dimension_literal)
                )
            self.conn.commit()
            columns.add("embedding")

        required: Set[str] = {"entity_id", "embedding", "text"}
        missing = required - columns
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(
                f"Table '{name}' is missing required columns: {missing_list}"
            )

    def _ensure_table_schema(self, table: str, dimension: Optional[int]) -> int:
        name = self._normalize_table(table)
        resolved_dimension = self._resolve_dimension(name, dimension)

        self._create_table_schema(name, resolved_dimension)
        self._ensure_embedding_column(name, resolved_dimension)
        current_dimension = self._table_vector_dimension_sync(name)
        if current_dimension is None:
            raise ValueError(
                f"Unable to determine embedding dimension for table '{name}'"
            )
        if current_dimension != resolved_dimension:
            dimension_literal = sql.SQL(str(int(resolved_dimension)))
            try:
                with self.conn.cursor() as cur:
                    cur.execute(
                        sql.SQL(
                            "ALTER TABLE {table} ALTER COLUMN embedding TYPE vector({dimension});"
                        ).format(table=sql.Identifier(name), dimension=dimension_literal)
                    )
                self.conn.commit()
                current_dimension = resolved_dimension
            except psycopg2.Error as exc:  # pragma: no cover - dependent on live database state
                self.conn.rollback()
                raise ValueError(
                    f"Failed to align embedding dimension for table '{name}' to {resolved_dimension}: {exc}"
                ) from exc
        return current_dimension

    async def ensure_table(self, table: str, dimension: Optional[int]) -> int:
        def _ensure() -> int:
            return self._ensure_table_schema(table, dimension)

        return await asyncio.to_thread(_ensure)

    async def ping(self) -> bool:
        def _ping() -> bool:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1;")
                return cur.fetchone() is not None

        return await asyncio.to_thread(_ping)

    async def list_tables(self) -> List[str]:
        def _list() -> List[str]:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                    """
                )
                rows = cur.fetchall()
            return [row["table_name"] for row in rows]

        return await asyncio.to_thread(_list)

    async def get_table_dimension(self, table: str) -> Optional[int]:
        name = self._ensure_table_exists(table)

        def _dimension() -> Optional[int]:
            columns = self._table_columns_sync(name)
            if "embedding" not in columns:
                raise ValueError(
                    f"Table '{name}' does not include an 'embedding' column required for vector operations"
                )
            return self._table_vector_dimension_sync(name)

        return await asyncio.to_thread(_dimension)

    async def insert_vectors(
        self,
        table: str,
        vectors: Iterable[dict],
    ) -> int:
        name = self._ensure_table_exists(table)

        def _insert() -> int:
            dimension = self._table_vector_dimension_sync(name)
            print(f"Dimension for table {name}: {dimension}")
            columns = self._table_columns_sync(name)
            print(f"Columns for table {name}: {columns}")
            if "embedding" not in columns:
                raise ValueError(
                    f"Table '{name}' does not include an 'embedding' column required for vector operations"
                )
            has_database_column = "database" in columns
            statement = sql.SQL(
                """
                INSERT INTO {table} (entity_id, embedding, text{database_column})
                VALUES (%s, %s, %s{database_placeholder})
                """
            ).format(
                table=sql.Identifier(name),
                database_column=sql.SQL(", database") if has_database_column else sql.SQL(""),
                database_placeholder=sql.SQL(", %s") if has_database_column else sql.SQL(""),
            )

            inserted = 0
            with self.conn.cursor() as cur:
                for record in vectors:
                    embedding = record.get("embedding")
                    print(f"Embedding for record {record.get('entity_id')}: {len(embedding)}")
                    if embedding is not None:
                        embedding = list(embedding)
                    if dimension and embedding is not None and len(embedding) != dimension:
                        raise ValueError(
                            f"Embedding dimension mismatch for table '{name}': expected {dimension}, got {len(embedding)}"
                        )
                    params: List[Any] = [
                        record.get("entity_id"),
                        embedding,
                        record.get("text"),
                    ]
                    if has_database_column:
                        params.append(record.get("database") or name)
                    cur.execute(statement, params)
                    inserted += 1
            self.conn.commit()
            return inserted

        return await asyncio.to_thread(_insert)

    async def execute_query(
        self,
        database: Optional[str],
        query: str,
        *,
        table: Optional[str] = None,
    ) -> List[List]:
        statement = query.strip()
        if not statement:
            return []

        def _execute() -> List[List]:
            self._verify_database(database)
            if table:
                self._ensure_table_exists(table)
            with self.conn.cursor() as cur:
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
        if result.table:
            plan = f"Target table: {result.table}\n\n{plan}"
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

    async def call_rag_chat(self, task: str, table: Optional[str]) -> List[dict]:
        result = await self._workflow.arun(task, table=table or None)
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
