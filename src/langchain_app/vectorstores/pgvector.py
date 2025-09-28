"""LangChain wrapper around the existing pgvector deployment."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from ..embeddings import get_embeddings
from ..settings import LangChainAppSettings


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RetrievalResult:
    """Structured result returned by the pgvector retriever."""

    text: str
    score: float
    metadata: dict


class PGVectorStore:
    """Utility class that encapsulates pgvector access through LangChain."""

    def __init__(self, settings: LangChainAppSettings) -> None:
        self._settings = settings
        self._store_cache: Dict[str, PGVector] = {}

    def _ensure_store(self, table: Optional[str] = None) -> PGVector:
        collection = table or self._settings.vector_table
        if collection not in self._store_cache:
            self._store_cache[collection] = PGVector(
                connection_string=self._settings.pg_connection_uri,
                collection_name=collection,
                embedding_function=get_embeddings(self._settings),
                use_jsonb=True,
            )
        return self._store_cache[collection]

    @property
    def retriever(self) -> VectorStoreRetriever:
        """Return a default retriever with the configured top-k."""

        return self.as_retriever()

    def as_retriever(
        self,
        *,
        table: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> VectorStoreRetriever:
        """Instantiate a retriever with optional metadata filtering."""

        store = self._ensure_store(table)
        search_kwargs = {"k": top_k or self._settings.default_top_k}
        return store.as_retriever(search_kwargs=search_kwargs)

    def similarity_search(
        self,
        query: str,
        *,
        table: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> List[RetrievalResult]:
        """Perform a semantic search over the stored embeddings."""

        try:
            retriever = self.as_retriever(table=table, top_k=top_k)
            documents: Iterable[Document] = retriever.invoke(query)
        except Exception as exc:  # pragma: no cover - best effort fallback for offline environments
            logger.warning("Vector store unavailable, proceeding without context: %s", exc)
            return []
        results: List[RetrievalResult] = []
        for doc in documents:
            metadata = dict(doc.metadata or {})
            score = metadata.pop("score", metadata.pop("similarity", 0.0))
            results.append(
                RetrievalResult(
                    text=doc.page_content,
                    score=float(score) if score is not None else 0.0,
                    metadata=metadata,
                )
            )
        return results
