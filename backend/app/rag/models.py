"""
Data models for RAG pipeline components.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Represents a chunk of a document for vector storage."""

    id: str
    document_id: int
    content: str
    chunk_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    """Represents a search query for the RAG pipeline."""

    query: str
    user_id: int
    max_results: int = 5
    similarity_threshold: float = 0.7
    filters: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    """Represents a search result from vector store."""

    chunk: DocumentChunk
    similarity_score: float
    rank: int

    class Config:
        from_attributes = True


class RAGResponse(BaseModel):
    """Represents the final RAG response."""

    query: str
    answer: str
    sources: List[SearchResult]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class ProcessingConfig(BaseModel):
    """Configuration for document processing."""

    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_chunks_per_document: int = 100

    class Config:
        from_attributes = True


class EmbeddingConfig(BaseModel):
    """Configuration for embedding generation."""

    model_name: str = "text-embedding-ada-002"
    dimensions: int = 1536
    batch_size: int = 32

    class Config:
        from_attributes = True

