"""Configuration helpers for the Starlite frontend."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class FrontendSettings:
    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8001")
    default_chunk_size: int = int(os.getenv("DEFAULT_CHUNK_SIZE", "1536"))
    pg_database: str = os.getenv("POSTGRESQL_DATABASE", "vector_db")
    embedding_model: str = os.getenv("GPT_EMBEDDING_ENGINE", "text-embedding-3-large")


__all__ = ["FrontendSettings"]
