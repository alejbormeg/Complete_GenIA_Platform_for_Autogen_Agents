"""Service layer providing vector embeddings, database access, and agent chat."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

import anyio
from openai import DefaultHttpxClient, OpenAI
import psycopg2
from psycopg2.extras import execute_values

from langchain_app import LangChainAppSettings, NL2SQLWorkflow
from . import schemas

logger = logging.getLogger(__name__)


class ChunkStrategy:
    """Utility class responsible for chunking raw text."""

    @staticmethod
    def chunk_fixed(text: str, chunk_size: int) -> List[str]:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        normalized = text.replace("\r\n", "\n").strip()
        if not normalized:
            return []

        chunks: List[str] = []
        for index in range(0, len(normalized), chunk_size):
            chunk = normalized[index : index + chunk_size].strip()
            if chunk:
                chunks.append(chunk)
        return chunks


class EmbeddingClient:
    """Thin wrapper around the OpenAI embeddings API."""

    def __init__(self) -> None:
        try:
            self._client = OpenAI()
        except TypeError as exc:
            if "proxies" not in str(exc):
                raise
            # Retry with an explicit httpx client to avoid proxy kwarg issues.
            self._client = OpenAI(http_client=DefaultHttpxClient())

    def create_embedding(self, text: str, model: str, dimensions: Optional[int]) -> List[float]:
        if not text:
            return []

        kwargs = {"model": model, "input": text}
        if dimensions and model == "text-embedding-3-large":
            kwargs["dimensions"] = dimensions

        response = self._client.embeddings.create(**kwargs)
        vector = list(response.data[0].embedding)
        if dimensions and len(vector) > dimensions:
            return vector[:dimensions]
        return vector


class TextVectorService:
    """Encapsulates text chunking and embedding generation logic."""

    def __init__(
        self,
        *,
        chunk_strategy: Optional[ChunkStrategy] = None,
        embedding_client: Optional[EmbeddingClient] = None,
    ) -> None:
        self._chunk_strategy = chunk_strategy or ChunkStrategy()
        self._embedding_client = embedding_client or EmbeddingClient()

    async def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        return await anyio.to_thread.run_sync(self._extract_text_from_pdf_sync, file_bytes)

    @staticmethod
    def _extract_text_from_pdf_sync(file_bytes: bytes) -> str:
        import fitz  # Import lazily to keep module import light

        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
        try:
            text_parts: List[str] = []
            for page in pdf_document:
                text_parts.append(page.get_text())
            return "\n".join(part.strip() for part in text_parts if part.strip())
        finally:
            pdf_document.close()

    async def compute_vectors(self, text: str, chunk_size: int, embedding_model: str) -> List[schemas.VectorRecord]:
        return await anyio.to_thread.run_sync(
            self._compute_vectors_sync,
            text,
            chunk_size,
            embedding_model,
        )

    def _compute_vectors_sync(self, text: str, chunk_size: int, embedding_model: str) -> List[schemas.VectorRecord]:
        chunks = self._chunk_strategy.chunk_fixed(text, chunk_size)
        vectors: List[schemas.VectorRecord] = []
        for index, chunk in enumerate(chunks):
            embedding = self._embedding_client.create_embedding(chunk, embedding_model, chunk_size)
            vectors.append(
                schemas.VectorRecord(
                    entity_id=index,
                    embedding=embedding,
                    text=chunk,
                )
            )
        return vectors


@dataclass(slots=True)
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


class PGVectorService:
    """Handles persistence and querying of vector embeddings in PostgreSQL."""

    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config

    def _connect(self, database: Optional[str] = None):
        params = dict(
            host=self._config.host,
            port=self._config.port,
            user=self._config.user,
            password=self._config.password,
            database=database or self._config.database,
        )
        return psycopg2.connect(**params)

    async def insert_vectors(
        self,
        chunk_size: int,
        vectors: Sequence[schemas.VectorRecord],
        database: Optional[str] = None,
    ) -> int:
        return await anyio.to_thread.run_sync(
            self._insert_vectors_sync,
            chunk_size,
            list(vectors),
            database,
        )

    def _insert_vectors_sync(
        self,
        chunk_size: int,
        vectors: List[schemas.VectorRecord],
        database: Optional[str],
    ) -> int:
        if not vectors:
            return 0

        table = f"vector_embeddings_{chunk_size}"
        rows = [(item.entity_id, item.embedding, item.text) for item in vectors]

        conn = self._connect()
        try:
            with conn.cursor() as cur:
                if database:
                    payload = [row + (database,) for row in rows]
                    execute_values(
                        cur,
                        f"INSERT INTO {table} (entity_id, embedding, text, database) VALUES %s",
                        payload,
                    )
                else:
                    execute_values(
                        cur,
                        f"INSERT INTO {table} (entity_id, embedding, text) VALUES %s",
                        rows,
                    )
            conn.commit()
        finally:
            conn.close()

        return len(rows)

    async def execute_query(self, database: Optional[str], query: str) -> List[List]:
        return await anyio.to_thread.run_sync(self._execute_query_sync, database, query)

    def _execute_query_sync(self, database: Optional[str], query: str) -> List[List]:
        conn = self._connect(database)
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
            conn.commit()
        finally:
            conn.close()
        return [list(row) for row in rows]

    async def list_vector_databases(self, chunk_size: int) -> List[str]:
        return await anyio.to_thread.run_sync(self._list_vector_databases_sync, chunk_size)

    def _list_vector_databases_sync(self, chunk_size: int) -> List[str]:
        table = f"vector_embeddings_{chunk_size}"
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT DISTINCT database FROM {table} WHERE database IS NOT NULL ORDER BY database"
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        return [row[0] for row in rows if row and row[0]]

    async def ping(self) -> bool:
        try:
            await anyio.to_thread.run_sync(self._ping_sync)
            return True
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Database ping failed: %s", exc)
            return False

    def _ping_sync(self) -> None:
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        finally:
            conn.close()


class AgentsChatService:
    """Facilitates interactions with the LangChain NL2SQL workflow."""

    def __init__(self, settings: Optional[LangChainAppSettings] = None) -> None:
        self._logger = logging.getLogger(__name__)
        self._settings = settings or LangChainAppSettings.from_env()
        self._workflow = NL2SQLWorkflow(self._settings)

    async def call_rag_chat(
        self,
        task: str,
        database: Optional[str],
    ) -> List[dict]:
        prompt = task.strip()
        db_filter = self._normalize_database(database)
        user_message = self._build_user_message(prompt, database)

        try:
            result = await self._workflow.arun(prompt, database=db_filter)
        except Exception as exc:  # pragma: no cover - runtime safeguard
            self._logger.exception("LangChain workflow failed")
            return [
                user_message,
                {
                    "role": "assistant",
                    "name": "FeedbackLoopAgent",
                    "content": f"Workflow execution failed: {exc}",
                },
            ]

        return self._build_messages(user_message, result)

    @staticmethod
    def _normalize_database(database: Optional[str]) -> Optional[str]:
        if not database:
            return None
        normalized = database.strip()
        if not normalized or normalized.lower() == "all":
            return None
        return normalized

    @staticmethod
    def _build_user_message(task: str, database: Optional[str]) -> dict:
        content = task
        if database:
            content = f"{task}\n\nTarget database: {database}"
        return {
            "role": "user",
            "name": "UserProxyAgent",
            "content": content,
        }

    @staticmethod
    def _build_messages(user_message: dict, result) -> List[dict]:
        messages: List[dict] = [user_message]

        if result.retrieved_context:
            messages.append(
                {
                    "role": "assistant",
                    "name": "PgVectorAgent",
                    "content": AgentsChatService._format_retrievals(result.retrieved_context),
                }
            )

        plan_text = result.plan.strip() if result.plan else "No plan generated."
        messages.append(
            {
                "role": "assistant",
                "name": "PlannerAgent",
                "content": plan_text,
            }
        )

        final_content = AgentsChatService._build_final_message(result)
        messages.append(
            {
                "role": "assistant",
                "name": "FeedbackLoopAgent",
                "content": final_content,
            }
        )

        return messages

    @staticmethod
    def _format_retrievals(chunks: Iterable[dict]) -> str:
        formatted: List[str] = []
        for index, chunk in enumerate(chunks, start=1):
            metadata = chunk.get("metadata") or {}
            metadata_str = ", ".join(f"{key}={value}" for key, value in metadata.items()) or "none"
            formatted.append(
                f"[{index}] score={chunk.get('score', 0.0):.4f}, metadata={metadata_str}\n{chunk.get('text', '')}".strip()
            )
        return "\n\n".join(formatted)

    @staticmethod
    def _build_final_message(result) -> str:
        sections: List[str] = []

        feedback = (result.feedback or "").strip()
        if feedback:
            sections.append(feedback)

        sql_query = (result.sql_query or "").strip()
        if sql_query:
            sections.append(f"```sql\n{sql_query}\n```")

        return "\n\n".join(sections) if sections else "No SQL generated."


@dataclass(slots=True)
class AppServices:
    vector_service: TextVectorService
    pgvector_service: PGVectorService
    agents_chat_service: AgentsChatService


def build_services() -> AppServices:
    config = DatabaseConfig(
        host=os.getenv("POSTGRESQL_HOST", "localhost"),
        port=int(os.getenv("POSTGRESQL_PORT", "5432")),
        user=os.getenv("POSTGRESQL_USER", "postgres"),
        password=os.getenv("POSTGRESQL_PASSWORD", ""),
        database=os.getenv("POSTGRESQL_DATABASE", "postgres"),
    )

    return AppServices(
        vector_service=TextVectorService(),
        pgvector_service=PGVectorService(config),
        agents_chat_service=AgentsChatService(),
    )
