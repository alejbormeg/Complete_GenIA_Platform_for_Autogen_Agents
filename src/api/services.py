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
from langchain_app.agents.chains import build_chat_model, build_report_chain
from langchain_app.settings import LangChainAppSettings

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
def _env(*keys: str, default: Optional[str] = None) -> Optional[str]:
    """Return the first non-empty environment value for the provided keys."""

    for key in keys:
        value = os.getenv(key)
        if value not in (None, ""):
            return value
    return default


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
            host=_env("POSTGRES_HOST", "POSTGRESQL_HOST", default="db"),
            port=int(_env("POSTGRES_PORT", "POSTGRESQL_PORT", default="5432")),
            db=_env("POSTGRES_DB", "POSTGRESQL_DATABASE", default="postgres"),
            user=_env("POSTGRES_USER", "POSTGRESQL_USER", default="postgres"),
            password=_env("POSTGRES_PASSWORD", "POSTGRESQL_PASSWORD", default="postgres"),
            sslmode=_env("POSTGRES_SSLMODE", "POSTGRESQL_SSLMODE"),
            application_name=_env("PGAPPNAME", default="backend"),
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
    def _split_markdown_sections(text: str) -> List[str]:
        sections: List[str] = []
        current: List[str] = []
        for line in text.splitlines():
            if line.lstrip().startswith("#") and current:
                section = "\n".join(current).strip()
                if section:
                    sections.append(section)
                current = [line]
            else:
                current.append(line)
        if current:
            section = "\n".join(current).strip()
            if section:
                sections.append(section)
        return sections

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

    async def _compute_embeddings(
        self,
        chunks: List[str],
        *,
        model: str,
        dimensions: Optional[int],
        start_entity_id: int = 0,
    ) -> List[dict]:
        records: List[dict] = []
        for offset, chunk in enumerate(chunks):
            embedding = await asyncio.to_thread(
                self._embed_chunk,
                text=chunk,
                model=model,
                dimensions=dimensions,
            )
            if dimensions and len(embedding) != dimensions:
                raise ValueError(
                    f"Embedding response dimension mismatch: requested {dimensions}, received {len(embedding)}"
                )
            records.append(
                {
                    "entity_id": start_entity_id + offset,
                    "embedding": embedding,
                    "text": chunk,
                }
            )
        return records

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
        if not chunks:
            return []
        return await self._compute_embeddings(
            chunks,
            model=embedding_model,
            dimensions=embed_dimensions,
        )

    async def compute_markdown_vectors(
        self,
        text: str,
        chunk_size: int,
        embedding_model: str,
        *,
        dimensions: Optional[int] = None,
    ) -> List[dict]:
        embed_dimensions = self._ensure_dimension(dimensions if dimensions is not None else chunk_size)
        chunk_words = max(1, chunk_size or embed_dimensions or 512)
        sections = self._split_markdown_sections(text)
        if not sections:
            raise ValueError("No usable content found in Markdown document")
        chunks: List[str] = []
        for section in sections:
            chunks.extend(self._chunk_text(section, chunk_words))
        chunks = [chunk for chunk in chunks if chunk.strip()]
        if not chunks:
            raise ValueError("Failed to extract text chunks from Markdown document")
        return await self._compute_embeddings(
            chunks,
            model=embedding_model,
            dimensions=embed_dimensions,
        )

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

    def _normalize_schema(self, schema: str) -> str:
        name = (schema or "").strip()
        if not name:
            raise ValueError("Schema name must not be empty")
        if not self.IDENTIFIER_PATTERN.fullmatch(name):
            raise ValueError(f"Invalid schema name '{schema}'")
        return name

    def _table_exists_sync(self, table: str, *, schema: str = "public") -> bool:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = %s
                ) AS present;
                """,
                (schema, table),
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

    def _ensure_table_exists(self, table: str, *, schema: str = "public") -> str:
        name = self._normalize_table(table)
        schema_name = self._normalize_schema(schema)
        if not self._table_exists_sync(name, schema=schema_name):
            raise ValueError(
                f"Table '{schema_name}.{name}' does not exist in database '{self.database_name}'"
            )
        return name

    def _table_columns_sync(self, table: str, *, schema: str = "public") -> List[str]:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position;
                """,
                (schema, table),
            )
            rows = cur.fetchall()
        return [row["column_name"] for row in rows]

    def _table_vector_dimension_sync(self, table: str, *, schema: str = "public") -> Optional[int]:
        qualified = f"{schema}.{table}"
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
                (qualified,),
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
            columns = self._table_columns_sync(name)
            if "embedding" not in columns:
                raise ValueError(
                    f"Table '{name}' does not include an 'embedding' column required for vector operations"
                )
            has_database_column = "database" in columns
            statement = sql.SQL(
                """
                INSERT INTO public.{table} (entity_id, embedding, text{database_column})
                VALUES (%s, %s, %s{database_placeholder})
                """
            ).format(
                table=sql.Identifier(name),
                database_column=sql.SQL(", database") if has_database_column else sql.SQL(""),
                database_placeholder=sql.SQL(", %s") if has_database_column else sql.SQL(""),
            )

            print(f"SQL query: {statement.as_string(self.conn)}")
            inserted = 0
            with self.conn.cursor() as cur:
                for record in vectors:
                    try:
                        embedding = record.get("embedding")
                        if embedding is not None:
                            # Ensure embedding is a list of floats
                            embedding = [float(x) for x in embedding]
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
                            # Use record["database"] if present, else None (NULL in DB)
                            params.append(record.get("database"))
                        print(f"SQL params: {params}")
                        cur.execute(statement, params)
                        # Run select command to confirm insertion
                        cur.execute(f"SELECT * FROM {name} WHERE entity_id = %s", (record.get("entity_id"),))
                        print(f"Inserted record: {cur.fetchall()}")
                        inserted += 1
                    except Exception as exc:
                        logger.error(f"Failed to insert vector record: {record}, error: {exc}")
            self.conn.commit()
            return inserted

        return await asyncio.to_thread(_insert)

    async def execute_query(
        self,
        database: Optional[str],
        query: str,
        *,
        table: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> tuple[list[str], list[list[Any]]]:
        statement = query.strip()
        if not statement:
            return [], []

        def _execute() -> tuple[list[str], list[list[Any]]]:
            target_db = database or self.database_name
            self._verify_database(target_db)
            schema_name = self._normalize_schema(schema) if schema else None
            if table:
                if schema_name:
                    self._ensure_table_exists(table, schema=schema_name)
                else:
                    self._ensure_table_exists(table)
            with self.conn.cursor() as cur:
                if schema_name:
                    search_path = sql.SQL(", ").join(
                        [sql.Identifier(schema_name), sql.Identifier("public")]
                    )
                    cur.execute(
                        sql.SQL("SET search_path TO {schema_list}").format(
                            schema_list=search_path
                        )
                    )
                cur.execute(statement)
                if cur.description is None:
                    if schema_name:
                        cur.execute("SET search_path TO DEFAULT")
                    self.conn.commit()
                    return [], []
                # Collect column names from cursor description
                columns = [d.name if hasattr(d, "name") else d[0] for d in cur.description]
                rows_dicts = cur.fetchall()
                if schema_name:
                    cur.execute("SET search_path TO DEFAULT")
            # Order row values by columns to keep deterministic alignment
            rows = [[row.get(col) for col in columns] for row in rows_dicts]
            return columns, rows

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
        for item in rows:
            text = (item.get("text") or "").strip()
            if len(text) > 220:
                text = text[:220].rstrip() + "…"
            score = item.get("score")
            score_str = f"{score:.4f}" if isinstance(score, (int, float)) else "n/a"
            metadata = item.get("metadata") or {}
            # Compact metadata summary
            meta_pairs = ", ".join(f"{k}={v}" for k, v in list(metadata.items())[:3]) or "none"
            formatted.append(f"- {text} (score: {score_str}; metadata: {meta_pairs})")
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


class ReportService:
    """Builds a Markdown report from question, SQL, and execution results."""

    def __init__(self, settings: Optional[LangChainAppSettings] = None) -> None:
        self.settings = settings or LangChainAppSettings.from_env()
        model = build_chat_model(self.settings)
        self._report = build_report_chain(model)

    @staticmethod
    def _escape_cell(value: Any) -> str:
        if value is None:
            return "∅"
        text = str(value)
        # Escape pipes to avoid breaking Markdown table structure
        return text.replace("|", "\\|")

    @classmethod
    def _to_markdown_table(
        cls, columns: List[str], rows: List[List[Any]], max_rows: int = 50
    ) -> str:
        cols = [cls._escape_cell(c) for c in (columns or [])]
        if not cols:
            # Fallback generic column headers
            max_len = max((len(r) for r in rows), default=0)
            cols = [f"col_{i+1}" for i in range(max_len)]
        header = "| " + " | ".join(cols) + " |"
        sep = "| " + " | ".join(["---"] * len(cols)) + " |"
        lines = [header, sep]
        for idx, row in enumerate(rows or []):
            if idx >= max_rows:
                lines.append(f"| … |" + (" |" * (len(cols) - 1)))
                break
            values = [cls._escape_cell(row[i] if i < len(row) else None) for i in range(len(cols))]
            lines.append("| " + " | ".join(values) + " |")
        return "\n".join(lines)

    def generate_markdown_report(
        self,
        *,
        question: str,
        sql_query: str,
        columns: List[str],
        rows: List[List[Any]],
        plan: Optional[str] = None,
        feedback: Optional[str] = None,
    ) -> tuple[str, str]:
        import datetime as _dt

        results_markdown = self._to_markdown_table(columns, rows)
        try:
            markdown = self._report.invoke(
                {
                    "question": question,
                    "sql_query": sql_query,
                    "results_markdown": results_markdown,
                    "plan": (plan or "").strip(),
                    "feedback": (feedback or "").strip(),
                }
            ).strip()
        except Exception as exc:  # pragma: no cover - fallback path
            logger.warning("Report LLM generation failed, using fallback: %s", exc)
            # Fallback determinista en español
            summary_rows = len(rows or [])
            markdown = (
                "## Informe NL→SQL\n\n"
                f"### Resumen ejecutivo\n- Filas mostradas: {summary_rows}\n- Columnas: {len(columns or [])}\n\n"
                f"### Interpretación de resultados\nLos datos se presentan para revisión ejecutiva. Para un análisis más profundo podrían requerirse segmentaciones o periodos adicionales.\n\n"
                f"### Pregunta\n{question}\n\n"
                f"### Consulta SQL\n```sql\n{sql_query}\n```\n\n"
                f"### Resultados\n{results_markdown}\n\n"
            )
            if plan:
                markdown += f"### Plan\n- {plan.replace('\n', '\n- ')}\n\n"
            if feedback:
                markdown += f"### Feedback\n- {feedback.replace('\n', '\n- ')}\n\n"
            markdown += "### Notas\nInforme generado automáticamente por GenIA Platform.\n"

        now = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"informe-nl2sql-{now}.md"
        return filename, markdown

    def markdown_to_html(self, markdown_text: str, title: str = "Informe NL→SQL") -> str:
        """Render Markdown to a styled HTML document suitable for PDF conversion."""
        # Convert Markdown -> HTML fragment
        try:
            import markdown as _md
            html_body = _md.markdown(
                markdown_text,
                extensions=[
                    "extra",  # includes tables, abbr, etc.
                    "toc",
                    "sane_lists",
                    "nl2br",
                    "fenced_code",
                ],
                output_format="xhtml1",
            )
        except Exception:
            # Minimal fallback if markdown package is missing; render as <pre>
            import html as _html
            html_body = f"<pre>{_html.escape(markdown_text)}</pre>"

        # Build full HTML with embedded CSS for a clean, executive look
        css = """
        :root { --ink:#0f172a; --muted:#475569; --border:#e2e8f0; --bg:#ffffff; --accent:#2563eb; }
        @page { size: A4; margin: 24mm 18mm 22mm 18mm; }
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji"; color: var(--ink); background: var(--bg); line-height: 1.5; font-size: 12.5pt; }
        header { border-bottom: 1px solid var(--border); margin-bottom: 18px; padding-bottom: 8px; }
        h1 { font-size: 22pt; margin: 0; }
        h2 { font-size: 16pt; margin: 16px 0 6px; }
        h3 { font-size: 13pt; margin: 14px 0 6px; }
        h4 { font-size: 12pt; margin: 12px 0 6px; }
        p { margin: 8px 0; }
        .muted { color: var(--muted); }
        .container { max-width: 800px; margin: 0 auto; }
        code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 10.5pt; }
        pre { background: #0b1020; color: #e5e7eb; padding: 12px 14px; border-radius: 6px; overflow: auto; border: 1px solid #0b1730; }
        code { background: #eef2ff; padding: 0 .25rem; border-radius: 4px; border: 1px solid #e0e7ff; }
        blockquote { margin: 10px 0; padding: 8px 12px; border-left: 3px solid #c7d2fe; background: #f8fafc; border-radius: 4px; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0 16px; font-size: 11.5pt; }
        th, td { border: 1px solid var(--border); padding: 8px 10px; vertical-align: top; }
        th { background: #f8fafc; text-align: left; }
        tbody tr:nth-child(even) { background: #fbfdff; }
        .footer { position: running(pageFooter); font-size: 10pt; color: var(--muted); }
        @page {
          @bottom-left { content: element(pageFooter); }
        }
        .page-number:after { content: counter(page); }
        .title-badge { color: var(--accent); font-weight: 600; letter-spacing: .02em; }
        """

        html = f"""
        <!DOCTYPE html>
        <html lang=\"es\">
          <head>
            <meta charset=\"utf-8\" />
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
            <title>{title}</title>
            <style>{css}</style>
          </head>
          <body>
            <div class=\"container\">
              <header>
                <div class=\"title-badge\">GenIA Platform</div>
                <h1>{title}</h1>
              </header>
              {html_body}
              <div class=\"footer\">Página <span class=\"page-number\"></span></div>
            </div>
          </body>
        </html>
        """
        return html

    def generate_pdf_from_markdown(self, markdown_text: str, pdf_title: str = "Informe NL→SQL") -> bytes:
        """Convert Markdown to a styled PDF using HTML rendering.

        Prefers WeasyPrint if available; otherwise attempts a basic fallback with PyMuPDF
        limited HTML support.
        """
        html = self.markdown_to_html(markdown_text, title=pdf_title)

        # Try WeasyPrint first for high-quality HTML→PDF rendering
        try:
            from weasyprint import HTML as _HTML
        except Exception:
            _HTML = None

        if _HTML is not None:
            try:
                pdf_bytes = _HTML(string=html, base_url=".").write_pdf()
                return pdf_bytes
            except Exception:
                pass

        # Fallback: render minimal HTML into PDF using PyMuPDF (already a dependency)
        try:
            import fitz  # PyMuPDF

            doc = fitz.open()
            page = doc.new_page(width=595.2, height=841.8)  # A4 @ 72dpi
            # Render HTML inside a page rectangle; long content will be clipped in this fallback.
            rect = fitz.Rect(36, 36, 559.2, 805.8)
            try:
                page.insert_htmlbox(rect, html)
            except Exception:
                # As a last resort, dump raw text
                page.insert_textbox(rect, markdown_text, fontsize=11, fontname="helv")
            pdf_bytes = doc.tobytes()
            doc.close()
            return pdf_bytes
        except Exception as exc:
            raise RuntimeError(f"Failed to render PDF: {exc}")

    def generate_pdf_report(
        self,
        *,
        question: str,
        sql_query: str,
        columns: List[str],
        rows: List[List[Any]],
        plan: Optional[str] = None,
        feedback: Optional[str] = None,
    ) -> tuple[str, bytes]:
        """Generate a PDF report and its filename."""
        filename_md, markdown = self.generate_markdown_report(
            question=question,
            sql_query=sql_query,
            columns=columns,
            rows=rows,
            plan=plan,
            feedback=feedback,
        )
        # Replace extension
        pdf_name = filename_md.rsplit(".", 1)[0] + ".pdf"
        pdf_bytes = self.generate_pdf_from_markdown(markdown, pdf_title="Reporte")
        return pdf_name, pdf_bytes


# ---------------------------------------------------------------------------
# Service container exposed to the FastAPI app
# ---------------------------------------------------------------------------


@dataclass
class AppServices:
    pg_conn: "psycopg2.extensions.connection"
    vector_service: VectorService
    pgvector_service: PGVectorService
    agents_chat_service: AgentsChatService
    report_service: ReportService


def build_services() -> AppServices:
    conn = open_pg_connection()
    vector_service = VectorService()
    pgvector_service = PGVectorService(conn)
    agents_chat_service = AgentsChatService()
    report_service = ReportService()
    return AppServices(
        pg_conn=conn,
        vector_service=vector_service,
        pgvector_service=pgvector_service,
        agents_chat_service=agents_chat_service,
        report_service=report_service,
    )
