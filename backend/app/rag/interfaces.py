"""
Abstract interfaces for RAG pipeline components.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any, Optional
from .models import (
    DocumentChunk,
    SearchQuery,
    SearchResult,
    RAGResponse,
    ProcessingConfig,
    EmbeddingConfig
)


class DocumentProcessor(ABC):
    """Abstract interface for document processing and chunking."""
    
    @abstractmethod
    async def process_document(self, document_id: int, content: str, config: ProcessingConfig) -> list[DocumentChunk]:
        """Process a document and return chunks."""
        pass
    
    @abstractmethod
    async def chunk_text(self, text: str, config: ProcessingConfig) -> list[str]:
        """Split text into chunks according to configuration."""
        pass


class EmbeddingService(ABC):
    """Abstract interface for embedding generation."""
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        pass
    
    @abstractmethod
    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in batch."""
        pass
    
    @abstractmethod
    async def get_config(self) -> EmbeddingConfig:
        """Get embedding service configuration."""
        pass


class VectorStore(ABC):
    """Abstract interface for vector storage."""
    
    @abstractmethod
    async def store_chunks(self, chunks: list[DocumentChunk]) -> bool:
        """Store document chunks with their embeddings."""
        pass
    
    @abstractmethod
    async def search_similar(self, query_embedding: list[float], limit: int, filters: Optional[dict[str, Any]] = None) -> list[SearchResult]:
        """Search for similar chunks using vector similarity."""
        pass
    
    @abstractmethod
    async def delete_document_chunks(self, document_id: int) -> bool:
        """Delete all chunks for a specific document."""
        pass
    
    @abstractmethod
    async def get_chunk_count(self, document_id: Optional[int] = None) -> int:
        """Get total number of chunks, optionally filtered by document."""
        pass


class SearchService(ABC):
    """Abstract interface for search operations."""
    
    @abstractmethod
    async def search(self, query: SearchQuery) -> list[SearchResult]:
        """Perform semantic search using the query."""
        pass
    
    @abstractmethod
    async def search_with_reranking(self, query: SearchQuery) -> list[SearchResult]:
        """Perform search with additional reranking."""
        pass


class ResponseGenerator(ABC):
    """Abstract interface for response generation."""
    
    @abstractmethod
    async def generate_response(self, query: str, context_chunks: list[DocumentChunk]) -> str:
        """Generate a response based on query and context chunks."""
        pass
    
    @abstractmethod
    async def generate_response_stream(self, query: str, context_chunks: list[DocumentChunk]) -> AsyncGenerator[str, None]:
        """Generate a streaming response based on query and context chunks."""
        pass


class RAGPipeline(ABC):
    """Abstract interface for the complete RAG pipeline."""
    
    @abstractmethod
    async def process_document(self, document_id: int, content: str) -> bool:
        """Process a document through the complete pipeline."""
        pass
    
    @abstractmethod
    async def query(self, search_query: SearchQuery) -> RAGResponse:
        """Query the RAG pipeline and return a response."""
        pass
    
    @abstractmethod
    async def query_stream(self, search_query: SearchQuery) -> AsyncGenerator[str, None]:
        """Query the RAG pipeline and return a streaming response."""
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: int) -> bool:
        """Delete a document and all its chunks from the pipeline."""
        pass
