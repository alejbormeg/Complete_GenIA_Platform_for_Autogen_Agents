"""Pydantic schemas for the Starlite interface."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class NL2SQLRequest(BaseModel):
    question: str = Field(..., description="User natural language request")
    database: Optional[str] = Field(
        default=None,
        description="Optional database identifier used to filter vector search",
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Override the number of vector matches to retrieve",
    )


class RetrievalChunk(BaseModel):
    text: str
    score: float
    metadata: Dict[str, Any]


class NL2SQLResponse(BaseModel):
    question: str
    database: Optional[str]
    plan: str
    sql_query: str
    feedback: str
    retrieved_context: List[RetrievalChunk]
