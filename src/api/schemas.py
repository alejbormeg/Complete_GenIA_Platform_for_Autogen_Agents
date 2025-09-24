"""Pydantic models for the FastAPI gateway."""

from __future__ import annotations

import os
from typing import Any, List, Optional

from pydantic import BaseModel, Field


DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "1536"))


class VectorRecord(BaseModel):
    entity_id: int = Field(..., ge=0)
    embedding: List[float]
    text: str


class ComputeVectorsRequest(BaseModel):
    text: str
    chunk_size: int = Field(..., gt=0)
    embedding_model: str


class ComputeVectorsResponse(BaseModel):
    vectors: List[VectorRecord]


class TextToVectorDbRequest(ComputeVectorsRequest):
    database: Optional[str] = None


class TextToVectorDbResponse(BaseModel):
    chunk_size: int
    database: Optional[str]
    records: int


class AgentsChatRequest(BaseModel):
    task: str
    database: Optional[str] = None


class AgentMessage(BaseModel):
    role: str
    name: str
    content: Optional[str] = None
    function_call: Optional[dict[str, Any]] = None


class AgentsChatResponse(BaseModel):
    messages: List[AgentMessage]


class ExecuteQueryRequest(BaseModel):
    query: str
    database: Optional[str] = None


class ExecuteQueryResponse(BaseModel):
    database: Optional[str]
    rows: List[List[Any]]


class UploadPdfResponse(BaseModel):
    chunk_size: int
    database: Optional[str]
    detail: str


class HealthResponse(BaseModel):
    status: str
    database_status: str


class VectorDatabasesResponse(BaseModel):
    chunk_size: int
    databases: List[str]
