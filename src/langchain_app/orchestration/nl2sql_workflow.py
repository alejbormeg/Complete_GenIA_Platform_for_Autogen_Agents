"""LangChain orchestration that mirrors the legacy Autogen multi-agent flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import anyio

from ..agents.chains import (
    build_chat_model,
    build_feedback_chain,
    build_planner_chain,
    build_sql_chain,
)
from ..settings import LangChainAppSettings
# ⬇️ Usamos la nueva API del vector store
from ..vectorstores.pgvector import retrieve, RetrievalResult


@dataclass(slots=True)
class NL2SQLResult:
    """Structured response produced by the LangChain workflow."""

    question: str
    table: Optional[str]
    plan: str
    sql_query: str
    feedback: str
    retrieved_context: List[Dict[str, Any]] = field(default_factory=list)


class NL2SQLWorkflow:
    """Co-ordinate retrieval, planning, SQL generation and feedback validation."""

    def __init__(
        self,
        settings: Optional[LangChainAppSettings] = None,
        *,
        # mantenemos el parámetro para compatibilidad, pero ya no se usa
        vector_store: Optional[object] = None,
    ) -> None:
        self.settings = settings or LangChainAppSettings.from_env()
        model = build_chat_model(self.settings)
        self._planner = build_planner_chain(model)
        self._sql = build_sql_chain(model)
        self._feedback = build_feedback_chain(model)

    def run(
        self,
        question: str,
        *,
        table: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> NL2SQLResult:
        k = top_k or getattr(self.settings, "pgvector_top_k", 5)

        default_vec_table = getattr(self.settings, "vector_table", "vector_embeddings_1536")
        if table and "vector_embeddings" in table:
            vec_table = table
            db_filter = None
        else:
            vec_table = default_vec_table
            db_filter = table  # p.ej. "financial"

        retrievals: List[RetrievalResult] = retrieve(
            self.settings,
            query=question,
            table=vec_table,
            database_filter=db_filter,
            k=k,
        )

        print(f"Retrieved {len(retrievals)} context documents from vector store")
        context = _format_context(retrievals)
        print("Formatted context for LLM:")
        print(context)

        plan = self._planner.invoke({"question": question, "context": context})
        sql_raw = self._sql.invoke({
            "question": question,
            "plan": plan,
            "context": context,
        })
        sql_query = _strip_termination(sql_raw)
        feedback_raw = self._feedback.invoke({
            "question": question,
            "plan": plan,
            "sql_query": sql_query,
            "context": context,
        })
        feedback = _strip_termination(feedback_raw)

        return NL2SQLResult(
            question=question,
            table=table,
            plan=plan.strip(),
            sql_query=sql_query.strip(),
            feedback=feedback.strip(),
            retrieved_context=[
                {
                    "text": item.text,
                    "score": item.score,
                    "metadata": item.metadata,
                }
                for item in retrievals
            ],
        )

    async def arun(
        self,
        question: str,
        *,
        table: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> NL2SQLResult:
        """Async wrapper compatible with Starlite."""
        from functools import partial
        runner = partial(self.run, question, table=table, top_k=top_k)
        return await anyio.to_thread.run_sync(runner)


def _format_context(retrievals: List[RetrievalResult]) -> str:
    if not retrievals:
        return "No relevant documents were found in the vector store."

    formatted = []
    for item in retrievals:
        meta = {k: v for k, v in item.metadata.items() if v is not None}
        meta_str = ", ".join(f"{key}={value}" for key, value in meta.items())
        formatted.append(
            f"Score: {item.score:.4f}\nMetadata: {meta_str or 'none'}\nContent: {item.text}"
        )
    return "\n\n".join(formatted)


def _strip_termination(message: str) -> str:
    """Remove the legacy 'Terminate' suffix while keeping SQL intact."""
    cleaned = message.strip()
    lower = cleaned.lower()
    if lower.endswith("terminate"):
        cleaned = cleaned[: -len("terminate")].rstrip(" -:\n")
    return cleaned
