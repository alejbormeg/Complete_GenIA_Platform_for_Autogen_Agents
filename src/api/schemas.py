"""Pydantic models for the FastAPI gateway."""

from __future__ import annotations

import os
from typing import Any, List, Optional

from pydantic import AliasChoices, BaseModel, Field
from pydantic.config import ConfigDict


DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "1536"))
DEFAULT_DATABASE = os.getenv("POSTGRESQL_DATABASE", "vector_db")


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


class TextToVectorDbRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text: str
    chunk_size: int = Field(DEFAULT_CHUNK_SIZE, gt=0)
    embedding_model: str
    table: str = Field(
        ...,
        min_length=1,
        validation_alias=AliasChoices("table", "database"),
        serialization_alias="table",
    )


class TextToVectorDbResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    chunk_size: int
    table: str = Field(..., serialization_alias="table")
    records: int


class AgentsChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    task: str
    table: Optional[str] = Field(default=None, alias="database")


class AgentMessage(BaseModel):
    role: str
    name: str
    content: Optional[str] = None
    function_call: Optional[dict[str, Any]] = None


class AgentsChatResponse(BaseModel):
    messages: List[AgentMessage]


class ExecuteQueryRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    query: str
    database: str = Field(DEFAULT_DATABASE, min_length=1)
    table: Optional[str] = Field(default=None)


class ExecuteQueryResponse(BaseModel):
    database: str
    table: Optional[str] = None
    # Column labels for the returned rows (may be empty for non-SELECT statements)
    columns: List[str] = Field(default_factory=list)
    # Row values ordered by the above columns
    rows: List[List[Any]]


class GenerateReportRequest(BaseModel):
    """Payload for generating a downloadable Markdown report."""

    question: str
    sql: str
    columns: List[str] = Field(default_factory=list)
    rows: List[List[Any]] = Field(default_factory=list)
    plan: Optional[str] = None
    feedback: Optional[str] = None


class GenerateReportResponse(BaseModel):
    filename: str
    markdown: str


class UploadMarkdownResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    chunk_size: int
    table: str
    database: str
    detail: str


class HealthResponse(BaseModel):
    status: str
    database_status: str


class VectorDatabasesResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tables: List[str] = Field(default_factory=list, alias="databases")
