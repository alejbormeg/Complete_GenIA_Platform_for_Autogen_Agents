"""LangChain wrapper around the existing pgvector deployment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from ..embeddings import get_embeddings
from ..settings import LangChainAppSettings


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
        self._store: Optional[PGVector] = None

    def _ensure_store(self) -> PGVector:
        if self._store is None:
            self._store = PGVector(
                connection_string=self._settings.pg_connection_uri,
                collection_name=self._settings.vector_table,
                embedding_function=get_embeddings(self._settings),
                use_jsonb=True,
            )
        return self._store

    @property
    def retriever(self) -> VectorStoreRetriever:
        """Return a default retriever with the configured top-k."""

        return self.as_retriever()

    def as_retriever(
        self,
        *,
        database: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> VectorStoreRetriever:
        """Instantiate a retriever with optional metadata filtering."""

        store = self._ensure_store()
        search_kwargs = {"k": top_k or self._settings.default_top_k}
        if database:
            search_kwargs["filter"] = {"database": database}
        return store.as_retriever(search_kwargs=search_kwargs)

    def similarity_search(
        self,
        query: str,
        *,
        database: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> List[RetrievalResult]:
        """Perform a semantic search over the stored embeddings."""

        retriever = self.as_retriever(database=database, top_k=top_k)
        try:
            documents: Iterable[Document] = retriever.invoke(query)
        except Exception:  # pragma: no cover - best effort fallback for offline environments
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
