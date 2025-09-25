"""Embedding factory compatible with the legacy Autogen configuration."""

from __future__ import annotations

from typing import Dict, Tuple

from langchain_openai import OpenAIEmbeddings

from .settings import LangChainAppSettings


_EMBEDDINGS_CACHE: Dict[Tuple[str, str, int], OpenAIEmbeddings] = {}


def get_embeddings(settings: LangChainAppSettings) -> OpenAIEmbeddings:
    """Return a cached embeddings client configured with the project defaults."""

    cache_key = (
        settings.openai_api_key or "",
        settings.embedding_model,
        settings.vector_dimensions,
    )
    embeddings = _EMBEDDINGS_CACHE.get(cache_key)
    if embeddings is None:
        embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
            dimensions=settings.vector_dimensions,
        )
        _EMBEDDINGS_CACHE[cache_key] = embeddings
    return embeddings
