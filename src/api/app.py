"""FastAPI gateway bridging external clients with Ray Serve deployments."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Iterable, List, Sequence

import ray
from fastapi import Depends, FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from ray import serve

try:  # Ray >= 2.49 renames DeploymentHandle
    from ray.serve.handle import RayServeDeploymentHandle as DeploymentHandle
except ImportError:  # pragma: no cover - fallback for older versions
    from ray.serve.handle import DeploymentHandle

from . import schemas

logger = logging.getLogger(__name__)
DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "1536"))


@dataclass
class RayServeHandles:
    text_to_vectors: DeploymentHandle
    pgvector: DeploymentHandle
    agents_chat: DeploymentHandle


def _normalize_vectors(raw_vectors: Iterable[Sequence]) -> List[schemas.VectorRecord]:
    """Convert raw tuples returned by Ray into structured records."""

    records: List[schemas.VectorRecord] = []
    for item in raw_vectors:
        try:
            entity_id, embedding, text = item
            records.append(
                schemas.VectorRecord(
                    entity_id=int(entity_id),
                    embedding=list(embedding),
                    text=str(text),
                )
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.warning("Failed to normalize vector entry %s: %s", item, exc)
    return records


def _normalize_rows(rows: Iterable[Sequence]) -> List[List]:
    return [list(row) for row in rows]


app = FastAPI(title="Ray Serve API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_handles(request: Request) -> RayServeHandles:
    handles: RayServeHandles | None = getattr(request.app.state, "handles", None)
    if not handles:
        raise HTTPException(status_code=503, detail="Ray handles are not ready")
    return handles


@app.on_event("startup")
async def startup() -> None:
    ray_address = os.getenv("RAY_ADDRESS", "ray://localhost:10001")
    if not ray.is_initialized():
        logger.info("Connecting to Ray at %s", ray_address)
        ray.init(address=ray_address)
    try:
        handles = RayServeHandles(
            text_to_vectors=serve.get_deployment_handle("Text2Vectors"),
            pgvector=serve.get_deployment_handle("PGVectorConnection"),
            agents_chat=serve.get_deployment_handle("RAGChatEndpoint"),
        )
        app.state.handles = handles
        app.state.ray_address = ray_address
    except Exception as exc:  # pragma: no cover - initialization failure should fail fast
        logger.exception("Failed to acquire Ray Serve handles")
        raise RuntimeError("Unable to connect to Ray Serve") from exc


@app.on_event("shutdown")
async def shutdown() -> None:
    if ray.is_initialized():
        logger.info("Disconnecting from Ray")
        ray.shutdown()


@app.get("/healthz", response_model=schemas.HealthResponse)
async def health(request: Request) -> schemas.HealthResponse:
    ray_address = getattr(request.app.state, "ray_address", "unknown")
    return schemas.HealthResponse(status="ok", ray_address=str(ray_address))


@app.post("/compute_vectors", response_model=schemas.ComputeVectorsResponse)
async def compute_vectors(
    payload: schemas.ComputeVectorsRequest,
    handles: RayServeHandles = Depends(get_handles),
) -> schemas.ComputeVectorsResponse:
    try:
        raw_vectors = await handles.text_to_vectors.compute_vectors.remote(payload.model_dump())
    except Exception as exc:  # pragma: no cover - runtime errors surfaced to clients
        logger.exception("Ray compute_vectors failed")
        raise HTTPException(status_code=502, detail=f"Failed to compute vectors: {exc}")
    return schemas.ComputeVectorsResponse(vectors=_normalize_vectors(raw_vectors))


@app.get("/vector_databases", response_model=schemas.VectorDatabasesResponse)
async def vector_databases(
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    handles: RayServeHandles = Depends(get_handles),
) -> schemas.VectorDatabasesResponse:
    try:
        databases = await handles.pgvector.list_vector_databases.remote(chunk_size)
    except Exception as exc:
        logger.exception("Ray vector_databases failed")
        raise HTTPException(status_code=502, detail=f"Failed to fetch databases: {exc}")

    return schemas.VectorDatabasesResponse(chunk_size=chunk_size, databases=list(databases))


@app.post("/text_to_vectordb", response_model=schemas.TextToVectorDbResponse)
async def text_to_vectordb(
    payload: schemas.TextToVectorDbRequest,
    handles: RayServeHandles = Depends(get_handles),
) -> schemas.TextToVectorDbResponse:
    try:
        raw_vectors = await handles.text_to_vectors.compute_vectors.remote(payload.model_dump())
        stored_vectors = await handles.pgvector.insert_into_db.remote(
            payload.chunk_size, raw_vectors, payload.database
        )
    except Exception as exc:
        logger.exception("Ray text_to_vectordb failed")
        raise HTTPException(status_code=502, detail=f"Failed to store vectors: {exc}")

    return schemas.TextToVectorDbResponse(
        chunk_size=payload.chunk_size,
        database=payload.database,
        records=len(stored_vectors),
    )


@app.post("/agents_chat", response_model=schemas.AgentsChatResponse)
async def agents_chat(
    payload: schemas.AgentsChatRequest,
    handles: RayServeHandles = Depends(get_handles),
) -> schemas.AgentsChatResponse:
    try:
        messages = await handles.agents_chat.call_rag_chat.remote(
            payload.task,
            payload.database,
        )
    except Exception as exc:
        logger.exception("Ray agents_chat failed")
        raise HTTPException(status_code=502, detail=f"Failed to execute agents_chat: {exc}")

    return schemas.AgentsChatResponse(messages=[schemas.AgentMessage.model_validate(m) for m in messages])


@app.post("/execute_query", response_model=schemas.ExecuteQueryResponse)
async def execute_query(
    payload: schemas.ExecuteQueryRequest,
    handles: RayServeHandles = Depends(get_handles),
) -> schemas.ExecuteQueryResponse:
    try:
        rows = await handles.pgvector.execute_query.remote(payload.database, payload.query)
    except Exception as exc:
        logger.exception("Ray execute_query failed")
        raise HTTPException(status_code=502, detail=f"Failed to execute query: {exc}")

    return schemas.ExecuteQueryResponse(database=payload.database, rows=_normalize_rows(rows))


@app.post("/upload_pdf", response_model=schemas.UploadPdfResponse)
async def upload_pdf(
    file: UploadFile,
    chunk_size: int = Form(...),
    embedding_model: str = Form(...),
    database: str | None = Form(default=None),
    handles: RayServeHandles = Depends(get_handles),
) -> schemas.UploadPdfResponse:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    request_payload = {
        "chunk_size": chunk_size,
        "embedding_model": embedding_model,
    }

    try:
        text = await handles.text_to_vectors.extract_text_from_pdf.remote(data)
        request_payload["text"] = text
        vectors = await handles.text_to_vectors.compute_vectors.remote(request_payload)
        await handles.pgvector.insert_into_db.remote(chunk_size, vectors, database)
    except Exception as exc:
        logger.exception("Ray upload_pdf failed")
        raise HTTPException(status_code=502, detail=f"Failed to process document: {exc}")

    return schemas.UploadPdfResponse(
        chunk_size=chunk_size,
        database=database,
        detail="Document uploaded successfully",
    )
