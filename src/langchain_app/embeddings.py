"""Embedding factory compatible with the legacy Autogen configuration."""

from __future__ import annotations

from functools import lru_cache
from langchain_openai import OpenAIEmbeddings

from .settings import LangChainAppSettings


@lru_cache(maxsize=1)
def get_embeddings(settings: LangChainAppSettings) -> OpenAIEmbeddings:
    """Return a cached embeddings client configured with the project defaults."""

    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
        dimensions=settings.vector_dimensions,
    )
