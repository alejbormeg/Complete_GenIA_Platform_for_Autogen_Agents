"""Runtime configuration for the LangChain orchestration layer."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Optional, Sequence


@dataclass(slots=True, frozen=True)
class LangChainAppSettings:
    """Configuration required to run the LangChain NL2SQL workflow."""

    openai_api_key: str
    chat_model: str
    embedding_model: str
    pg_host: str
    pg_port: int
    pg_user: str
    pg_password: str
    pg_database: str
    vector_table: str = "vector_embeddings_1536"
    vector_dimensions: int = 1536
    default_top_k: int = 3

    @classmethod
    def from_env(cls) -> "LangChainAppSettings":
        """Build settings from environment variables."""

        missing: list[str] = []

        def _env(keys: Sequence[str] | str, default: Optional[str] = None) -> Optional[str]:
            candidates = (keys,) if isinstance(keys, str) else tuple(keys)
            for key in candidates:
                value = os.getenv(key)
                if value is not None:
                    return value
            if default is None:
                missing.append(candidates[0])
            return default

        settings = cls(
            openai_api_key=_env("OPENAI_API_KEY", ""),
            chat_model=_env("GPT_MODEL", "gpt-4o-mini"),
            embedding_model=_env("GPT_EMBEDDING_ENGINE", "text-embedding-3-large"),
            pg_host=_env(("POSTGRESQL_HOST", "POSTGRES_HOST"), "localhost"),
            pg_port=int(_env(("POSTGRESQL_PORT", "POSTGRES_PORT"), "5432")),
            pg_user=_env(("POSTGRESQL_USER", "POSTGRES_USER"), "postgres"),
            pg_password=_env(("POSTGRESQL_PASSWORD", "POSTGRES_PASSWORD"), ""),
            pg_database=_env(("POSTGRESQL_DATABASE", "POSTGRES_DB"), "postgres"),
            vector_table=_env("PGVECTOR_TABLE", "vector_embeddings_1536"),
            vector_dimensions=int(_env("PGVECTOR_DIMENSIONS", "1536")),
            default_top_k=int(_env("PGVECTOR_TOP_K", "3")),
        )

        if missing and any(os.getenv(key) is None for key in missing):
            missing_keys = ", ".join(sorted(set(missing)))
            raise EnvironmentError(
                f"Missing required environment variables for LangChain settings: {missing_keys}"
            )

        return settings

    @property
    def pg_connection_uri(self) -> str:
        """Return a SQLAlchemy-compatible PostgreSQL connection URI."""

        return (
            "postgresql+psycopg2://"
            f"{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_database}"
        )

    def override(self, **kwargs: object) -> "LangChainAppSettings":
        """Return a copy of the settings with the provided overrides."""

        data = self.__dict__.copy()
        data.update(kwargs)
        return LangChainAppSettings(**data)
