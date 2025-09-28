"""FastAPI gateway providing vector operations and agent orchestration endpoints."""

from __future__ import annotations

import logging
import json

from fastapi import Depends, FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect

from . import schemas
from .services import AppServices, build_services

logger = logging.getLogger(__name__)
DEFAULT_CHUNK_SIZE = schemas.DEFAULT_CHUNK_SIZE
VECTOR_EMBEDDINGS_TABLE = "vector_embeddings_1536"
VECTOR_EMBEDDINGS_DIMENSION = 1536


app = FastAPI(title="GenIA API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_services(request: Request) -> AppServices:
    services: AppServices | None = getattr(request.app.state, "services", None)
    if not services:
        raise HTTPException(status_code=503, detail="Services are not ready")
    return services


@app.on_event("startup")
async def startup() -> None:
    app.state.services = build_services()


@app.on_event("shutdown")
async def shutdown() -> None:
    app.state.pop("services", None)


@app.get("/healthz", response_model=schemas.HealthResponse)
async def health(services: AppServices = Depends(get_services)) -> schemas.HealthResponse:
    database_ok = await services.pgvector_service.ping()
    status = "ok" if database_ok else "degraded"
    return schemas.HealthResponse(status=status, database_status="ok" if database_ok else "error")


@app.post("/compute_vectors", response_model=schemas.ComputeVectorsResponse)
async def compute_vectors(
    payload: schemas.ComputeVectorsRequest,
    services: AppServices = Depends(get_services),
) -> schemas.ComputeVectorsResponse:
    try:
        vectors = await services.vector_service.compute_vectors(
            payload.text,
            payload.chunk_size,
            payload.embedding_model,
        )
    except Exception as exc:  # pragma: no cover - exposed as 502 to clients
        logger.exception("Vector computation failed")
        raise HTTPException(status_code=502, detail=f"Failed to compute vectors: {exc}")
    return schemas.ComputeVectorsResponse(vectors=vectors)


@app.get("/vector_databases", response_model=schemas.VectorDatabasesResponse)
async def vector_databases(
    chunk_size: int | None = DEFAULT_CHUNK_SIZE,
    services: AppServices = Depends(get_services),
) -> schemas.VectorDatabasesResponse:
    _ = chunk_size  # legacy compatibility; value is ignored in the new implementation
    try:
        tables = await services.pgvector_service.list_tables()
    except Exception as exc:
        logger.exception("Failed to list vector databases")
        raise HTTPException(status_code=502, detail=f"Failed to fetch databases: {exc}")

    return schemas.VectorDatabasesResponse(tables=tables)


@app.post("/text_to_vectordb", response_model=schemas.TextToVectorDbResponse)
async def text_to_vectordb(
    payload: schemas.TextToVectorDbRequest,
    services: AppServices = Depends(get_services),
) -> schemas.TextToVectorDbResponse:
    try:
        dimension = await services.pgvector_service.ensure_table(
            payload.table,
            payload.chunk_size,
        )
        vectors = await services.vector_service.compute_vectors(
            payload.text,
            payload.chunk_size,
            payload.embedding_model,
            dimensions=dimension,
        )
        # Ensure dimensions match
        for vec in vectors:
            if len(vec["embedding"]) != dimension:
                raise ValueError(
                    f"Computed vector has {len(vec['embedding'])} dimensions, expected {dimension}"
                )
        stored = await services.pgvector_service.insert_vectors(payload.table, vectors)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to store vectors in pgvector")
        raise HTTPException(status_code=502, detail=f"Failed to store vectors: {exc}")

    return schemas.TextToVectorDbResponse(
        chunk_size=payload.chunk_size,
        table=payload.table,
        records=stored,
    )


@app.post("/agents_chat", response_model=schemas.AgentsChatResponse)
async def agents_chat(
    payload: schemas.AgentsChatRequest,
    services: AppServices = Depends(get_services),
) -> schemas.AgentsChatResponse:
    try:
        messages = await services.agents_chat_service.call_rag_chat(
            payload.task,
            payload.table,
        )
    except Exception as exc:
        logger.exception("Agents chat failed")
        raise HTTPException(status_code=502, detail=f"Failed to execute agents_chat: {exc}")

    return schemas.AgentsChatResponse(
        messages=[schemas.AgentMessage.model_validate(message) for message in messages]
    )


@app.post("/execute_query", response_model=schemas.ExecuteQueryResponse)
async def execute_query(
    payload: schemas.ExecuteQueryRequest,
    services: AppServices = Depends(get_services),
) -> schemas.ExecuteQueryResponse:
    try:
        rows = await services.pgvector_service.execute_query(
            payload.database,
            payload.query,
            table=payload.table,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to execute query")
        raise HTTPException(status_code=502, detail=f"Failed to execute query: {exc}")

    return schemas.ExecuteQueryResponse(
        database=payload.database,
        table=payload.table,
        rows=rows,
    )


@app.post("/upload_md", response_model=schemas.UploadMarkdownResponse)
async def upload_md(
    file: UploadFile,
    chunk_size: int = Form(...),
    embedding_model: str = Form(...),
    database: str = Form(...),
    services: AppServices = Depends(get_services),
) -> schemas.UploadMarkdownResponse:
    filename = (file.filename or "").lower()
    if not filename.endswith((".md", ".markdown")):
        raise HTTPException(status_code=400, detail="Only Markdown files (.md, .markdown) are supported")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Markdown file must be valid UTF-8 text") from exc

    if not text.strip():
        raise HTTPException(status_code=400, detail="Uploaded Markdown document has no textual content")

    db_value = database.strip()
    if not db_value:
        raise HTTPException(status_code=400, detail="Database value must not be empty")

    try:
        dimension = await services.pgvector_service.ensure_table(
            VECTOR_EMBEDDINGS_TABLE,
            VECTOR_EMBEDDINGS_DIMENSION,
        )
        vectors = await services.vector_service.compute_markdown_vectors(
            text,
            chunk_size,
            embedding_model,
            dimensions=dimension,
        )
        for record in vectors:
            record["database"] = db_value
        stored = await services.pgvector_service.insert_vectors(VECTOR_EMBEDDINGS_TABLE, vectors)
        if stored == 0:
            raise ValueError("No vectors were generated from the Markdown document")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to process uploaded Markdown document")
        raise HTTPException(status_code=502, detail=f"Failed to process document: {exc}")

    return schemas.UploadMarkdownResponse(
        chunk_size=chunk_size,
        table=VECTOR_EMBEDDINGS_TABLE,
        database=db_value,
        detail="Markdown document uploaded successfully",
    )


@app.websocket("/ws/agents_chat")
async def ws_agents_chat(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            # Espera un mensaje JSON: {"task": "...", "database": "opcional"}
            raw = await ws.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"type": "error", "message": "JSON inválido"})
                continue

            task = (payload.get("task") or "").strip()
            table = payload.get("table") or payload.get("database")

            if not task:
                await ws.send_json({"type": "error", "message": "Falta 'task'"})
                continue

            # Recupera el contenedor de servicios creado en startup
            services = getattr(app.state, "services", None)
            if services is None:
                await ws.send_json({"type": "error", "message": "Servicios no listos"})
                continue

            # Cabecera de inicio
            await ws.send_json({"type": "start", "mode": "agents"})

            # Ejecuta tu mismo flujo NL→SQL y devuelve mensajes "uno a uno"
            try:
                messages = await services.agents_chat_service.call_rag_chat(task, table)
                # messages es una lista de dicts con: role, name, content, function_call (según tu esquema)
                for msg in messages:
                    await ws.send_json({"type": "message", "data": msg})
                await ws.send_json({"type": "end"})
            except Exception as e:
                await ws.send_json({"type": "error", "message": f"{e}"})

    except WebSocketDisconnect:
        # El cliente cerró la conexión
        return
    except Exception as e:
        # Error inesperado
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        finally:
            await ws.close(code=1011)
