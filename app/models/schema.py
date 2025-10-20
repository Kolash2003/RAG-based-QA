from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class UploadResponse(BaseModel):
    """Response model for file upload."""
    document_id: str
    filename: str
    num_chunks: int
    message: str
    uploaded_at: str


class QueryRequest(BaseModel):
    """Request model for question answering."""
    question: str = Field(..., min_length=1, max_length=1000)
    top_k: Optional[int] = Field(None, ge=1, le=20)


class SourceDocument(BaseModel):
    """Model for source document in query response."""
    text: str
    metadata: Dict
    relevance_score: float


class QueryResponse(BaseModel):
    """Response model for question answering."""
    question: str
    answer: str
    sources: List[SourceDocument]
    num_sources: int


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str
    vector_store: Dict


class CollectionInfo(BaseModel):
    """Collection information model."""
    name: str
    count: int
    status: str