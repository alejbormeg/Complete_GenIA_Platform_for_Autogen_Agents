from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ray import serve

from langchain_app import LangChainAppSettings, NL2SQLWorkflow
from langchain_app.orchestration.nl2sql_workflow import NL2SQLResult


@serve.deployment()
class RAGChatEndpoint:
    """Ray Serve deployment that proxies the LangChain NL2SQL workflow."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.settings = LangChainAppSettings.from_env()
        self.workflow = NL2SQLWorkflow(self.settings)

    async def call_rag_chat(
        self,
        task: str,
        database: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Execute the LangChain NL2SQL workflow and return chat-like messages."""

        prompt = task.strip()
        db_filter = self._normalize_database(database)

        user_message = self._build_user_message(prompt, database)

        try:
            result = await self.workflow.arun(
                prompt,
                database=db_filter,
            )
        except Exception as exc:  # pragma: no cover - defensive fallback for runtime issues
            self.logger.exception("LangChain workflow failed")
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
    def _build_user_message(task: str, database: Optional[str]) -> Dict[str, Any]:
        content = task
        if database:
            content = f"{task}\n\nTarget database: {database}"
        return {
            "role": "user",
            "name": "UserProxyAgent",
            "content": content,
        }

    def _build_messages(
        self,
        user_message: Dict[str, Any],
        result: NL2SQLResult,
    ) -> List[Dict[str, Any]]:
        messages: List[Dict[str, Any]] = [user_message]

        if result.retrieved_context:
            messages.append(
                {
                    "role": "assistant",
                    "name": "PgVectorAgent",
                    "content": self._format_retrievals(result.retrieved_context),
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

        final_content = self._build_final_message(result)
        messages.append(
            {
                "role": "assistant",
                "name": "FeedbackLoopAgent",
                "content": final_content,
            }
        )

        return messages

    @staticmethod
    def _format_retrievals(chunks: List[Dict[str, Any]]) -> str:
        formatted: List[str] = []
        for index, chunk in enumerate(chunks, start=1):
            metadata = chunk.get("metadata") or {}
            metadata_str = ", ".join(f"{key}={value}" for key, value in metadata.items()) or "none"
            formatted.append(
                f"[{index}] score={chunk.get('score', 0.0):.4f}, metadata={metadata_str}\n{chunk.get('text', '')}".strip()
            )
        return "\n\n".join(formatted)

    @staticmethod
    def _build_final_message(result: NL2SQLResult) -> str:
        sections: List[str] = []

        feedback = (result.feedback or "").strip()
        if feedback:
            sections.append(feedback)

        sql_query = (result.sql_query or "").strip()
        if sql_query:
            sections.append(f"```sql\n{sql_query}\n```")

        return "\n\n".join(sections) if sections else "No SQL generated."

