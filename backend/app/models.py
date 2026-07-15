"""Pydantic models for request/response validation."""

from typing import List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for Q&A queries."""

    question: str = Field(..., min_length=1, max_length=1000, description="The question to ask")
    top_k: int = Field(
        default=5, ge=1, le=20, description="Number of top documents to retrieve"
    )


class QueryResponse(BaseModel):
    """Response model for Q&A queries."""

    question: str
    answer: str
    sources: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class DocumentUpload(BaseModel):
    """Request model for document uploads."""

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    metadata: Optional[dict] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    message: Optional[str] = None
