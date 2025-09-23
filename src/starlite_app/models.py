"""Request and response models for the Starlite frontend."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    task: str
    database: Optional[str] = Field(default=None, description="Optional dataset label to guide the agents")


class ChatResponse(BaseModel):
    messages: List[dict]


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    rows: List[List]


class UploadResponse(BaseModel):
    detail: str
    database: Optional[str] = None
    chunk_size: int


__all__ = [
    "ChatRequest",
    "ChatResponse",
    "QueryRequest",
    "QueryResponse",
    "UploadResponse",
]
