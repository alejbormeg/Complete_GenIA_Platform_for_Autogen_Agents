"""FastAPI gateway providing vector operations and agent orchestration endpoints."""

from __future__ import annotations

import logging

from fastapi import Depends, FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import schemas
from .services import AppServices, build_services

logger = logging.getLogger(__name__)
DEFAULT_CHUNK_SIZE = schemas.DEFAULT_CHUNK_SIZE


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
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    services: AppServices = Depends(get_services),
) -> schemas.VectorDatabasesResponse:
    try:
        databases = await services.pgvector_service.list_vector_databases(chunk_size)
    except Exception as exc:
        logger.exception("Failed to list vector databases")
        raise HTTPException(status_code=502, detail=f"Failed to fetch databases: {exc}")

    return schemas.VectorDatabasesResponse(chunk_size=chunk_size, databases=databases)


@app.post("/text_to_vectordb", response_model=schemas.TextToVectorDbResponse)
async def text_to_vectordb(
    payload: schemas.TextToVectorDbRequest,
    services: AppServices = Depends(get_services),
) -> schemas.TextToVectorDbResponse:
    try:
        vectors = await services.vector_service.compute_vectors(
            payload.text,
            payload.chunk_size,
            payload.embedding_model,
        )
        stored = await services.pgvector_service.insert_vectors(
            payload.chunk_size,
            vectors,
            payload.database,
        )
    except Exception as exc:
        logger.exception("Failed to store vectors in pgvector")
        raise HTTPException(status_code=502, detail=f"Failed to store vectors: {exc}")

    return schemas.TextToVectorDbResponse(
        chunk_size=payload.chunk_size,
        database=payload.database,
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
            payload.database,
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
        rows = await services.pgvector_service.execute_query(payload.database, payload.query)
    except Exception as exc:
        logger.exception("Failed to execute query")
        raise HTTPException(status_code=502, detail=f"Failed to execute query: {exc}")

    return schemas.ExecuteQueryResponse(database=payload.database, rows=rows)


@app.post("/upload_pdf", response_model=schemas.UploadPdfResponse)
async def upload_pdf(
    file: UploadFile,
    chunk_size: int = Form(...),
    embedding_model: str = Form(...),
    database: str | None = Form(default=None),
    services: AppServices = Depends(get_services),
) -> schemas.UploadPdfResponse:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        text = await services.vector_service.extract_text_from_pdf(data)
        vectors = await services.vector_service.compute_vectors(text, chunk_size, embedding_model)
        await services.pgvector_service.insert_vectors(chunk_size, vectors, database)
    except Exception as exc:
        logger.exception("Failed to process uploaded document")
        raise HTTPException(status_code=502, detail=f"Failed to process document: {exc}")

    return schemas.UploadPdfResponse(
        chunk_size=chunk_size,
        database=database,
        detail="Document uploaded successfully",
    )
