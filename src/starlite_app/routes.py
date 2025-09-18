"""Starlite endpoints exposing the LangChain NL2SQL workflow."""

from __future__ import annotations

from typing import Any, List

from starlite import Provide, Router, WebSocket, WebSocketDisconnect, get, post, websocket

from langchain_app import LangChainAppSettings, NL2SQLWorkflow

from .models import NL2SQLRequest, NL2SQLResponse, RetrievalChunk


def _convert_chunks(chunks: List[dict]) -> List[RetrievalChunk]:
    return [RetrievalChunk.model_validate(chunk) for chunk in chunks]


def build_router(
    *,
    settings: LangChainAppSettings,
    workflow: NL2SQLWorkflow,
) -> Router:
    """Create a router with REST and WebSocket handlers."""

    dependencies = {
        "settings": Provide(lambda: settings),
        "workflow": Provide(lambda: workflow),
    }

    @get("/healthz")
    async def health(settings: LangChainAppSettings) -> dict[str, Any]:
        return {
            "status": "ok",
            "model": settings.chat_model,
            "vector_table": settings.vector_table,
        }

    @post("/chat/nl2sql")
    async def chat_endpoint(
        data: NL2SQLRequest,
        workflow: NL2SQLWorkflow,
    ) -> NL2SQLResponse:
        result = await workflow.arun(
            data.question,
            database=data.database,
            top_k=data.top_k,
        )
        return NL2SQLResponse(
            question=result.question,
            database=result.database,
            plan=result.plan,
            sql_query=result.sql_query,
            feedback=result.feedback,
            retrieved_context=_convert_chunks(result.retrieved_context),
        )

    @websocket("/ws/nl2sql")
    async def websocket_endpoint(
        socket: WebSocket,
        workflow: NL2SQLWorkflow,
    ) -> None:
        await socket.accept()
        try:
            payload = await socket.receive_json()
            data = NL2SQLRequest.model_validate(payload)
            result = await workflow.arun(
                data.question,
                database=data.database,
                top_k=data.top_k,
            )
            await socket.send_json(
                NL2SQLResponse(
                    question=result.question,
                    database=result.database,
                    plan=result.plan,
                    sql_query=result.sql_query,
                    feedback=result.feedback,
                    retrieved_context=_convert_chunks(result.retrieved_context),
                ).model_dump()
            )
        except WebSocketDisconnect:
            pass
        finally:
            await socket.close()

    return Router(path="", route_handlers=[health, chat_endpoint, websocket_endpoint], dependencies=dependencies)
