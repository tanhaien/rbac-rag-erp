"""
RAG pipeline service implementation.
"""

import asyncio
import time
import uuid
from collections.abc import AsyncGenerator
from typing import Any, Dict, List, Optional

from ..core.config import get_settings
from .interfaces import (
    DocumentProcessor,
    EmbeddingService,
    RAGPipeline,
    ResponseGenerator,
    SearchService,
    VectorStore,
)
from .models import (
    DocumentChunk,
    EmbeddingConfig,
    ProcessingConfig,
    RAGResponse,
    SearchQuery,
    SearchResult,
)
from .real_services import (
    AdvancedDocumentProcessor,
    FAISSVectorStore,
    LLMResponseGenerator,
    RealSearchService,
    SentenceTransformerEmbeddingService,
)


class SimpleDocumentProcessor(DocumentProcessor):
    """Simple document processor implementation."""

    async def process_document(
        self, document_id: int, content: str, config: ProcessingConfig
    ) -> List[DocumentChunk]:
        """Process a document and return chunks."""
        chunks = await self.chunk_text(content, config)

        document_chunks = []
        for i, chunk_content in enumerate(chunks):
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=document_id,
                content=chunk_content,
                chunk_index=i,
                metadata={"chunk_size": len(chunk_content)},
            )
            document_chunks.append(chunk)

        return document_chunks

    async def chunk_text(self, text: str, config: ProcessingConfig) -> List[str]:
        """Split text into chunks according to configuration."""
        if len(text) <= config.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + config.chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start, end - 100), -1):
                    if text[i] in ".!?":
                        end = i + 1
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - config.chunk_overlap
            if start >= len(text):
                break

        return chunks[: config.max_chunks_per_document]


class MockEmbeddingService(EmbeddingService):
    """Mock embedding service for development."""

    def __init__(self, dimensions: int = 1536):
        self.dimensions = dimensions
        self.config = EmbeddingConfig(dimensions=dimensions)

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate mock embedding for a single text."""
        # Return random embedding for now
        import random

        return [random.uniform(-1, 1) for _ in range(self.dimensions)]

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings for multiple texts in batch."""
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings

    async def get_config(self) -> EmbeddingConfig:
        """Get embedding service configuration."""
        return self.config


class MockVectorStore(VectorStore):
    """Mock vector store for development."""

    def __init__(self):
        self.chunks: Dict[str, DocumentChunk] = {}
        self.embeddings: Dict[str, List[float]] = {}

    async def store_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """Store document chunks with their embeddings."""
        for chunk in chunks:
            self.chunks[chunk.id] = chunk
            if chunk.embedding:
                self.embeddings[chunk.id] = chunk.embedding
        return True

    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar chunks using vector similarity."""
        # Mock similarity search - return random results
        import random

        results = []
        available_chunks = list(self.chunks.values())

        if filters and "document_id" in filters:
            available_chunks = [
                c for c in available_chunks if c.document_id == filters["document_id"]
            ]

        for i in range(min(limit, len(available_chunks))):
            chunk = random.choice(available_chunks)
            score = random.uniform(0.5, 1.0)
            result = SearchResult(chunk=chunk, similarity_score=score, rank=i + 1)
            results.append(result)

        return sorted(results, key=lambda x: x.similarity_score, reverse=True)

    async def delete_document_chunks(self, document_id: int) -> bool:
        """Delete all chunks for a specific document."""
        chunks_to_delete = [
            chunk_id
            for chunk_id, chunk in self.chunks.items()
            if chunk.document_id == document_id
        ]
        for chunk_id in chunks_to_delete:
            del self.chunks[chunk_id]
            if chunk_id in self.embeddings:
                del self.embeddings[chunk_id]
        return True

    async def get_chunk_count(self, document_id: Optional[int] = None) -> int:
        """Get total number of chunks, optionally filtered by document."""
        if document_id is None:
            return len(self.chunks)
        return len([c for c in self.chunks.values() if c.document_id == document_id])


class MockSearchService(SearchService):
    """Mock search service implementation."""

    def __init__(self, vector_store: VectorStore, embedding_service: EmbeddingService):
        self.vector_store = vector_store
        self.embedding_service = embedding_service

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform semantic search using the query."""
        query_embedding = await self.embedding_service.generate_embedding(query.query)
        return await self.vector_store.search_similar(
            query_embedding, query.max_results, query.filters
        )

    async def search_with_reranking(self, query: SearchQuery) -> List[SearchResult]:
        """Perform search with additional reranking."""
        # For now, just use basic search
        return await self.search(query)


class MockResponseGenerator(ResponseGenerator):
    """Mock response generator for development."""

    async def generate_response(
        self, query: str, context_chunks: List[DocumentChunk]
    ) -> str:
        """Generate a mock response based on query and context chunks."""
        context_text = "\n".join([chunk.content for chunk in context_chunks])
        return f"Based on the provided context, here is a response to your query '{query}':\n\n{context_text[:500]}..."

    async def generate_response_stream(
        self, query: str, context_chunks: List[DocumentChunk]
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming mock response."""
        response = await self.generate_response(query, context_chunks)
        words = response.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.1)  # Simulate streaming


def create_document_processor() -> DocumentProcessor:
    """Create document processor based on configuration."""
    settings = get_settings()
    if settings.rag_use_real_services:
        return AdvancedDocumentProcessor()
    return SimpleDocumentProcessor()


def create_embedding_service() -> EmbeddingService:
    """Create embedding service based on configuration."""
    settings = get_settings()
    if settings.rag_use_real_services:
        return SentenceTransformerEmbeddingService(settings.rag_embedding_model)
    return MockEmbeddingService()


def create_vector_store() -> VectorStore:
    """Create vector store based on configuration."""
    settings = get_settings()
    if settings.rag_use_real_services:
        embedding_service = create_embedding_service()
        # Get dimensions from embedding service config
        config = asyncio.run(embedding_service.get_config())
        return FAISSVectorStore(config.dimensions, settings.rag_faiss_index_path)
    return MockVectorStore()


def create_search_service() -> SearchService:
    """Create search service based on configuration."""
    vector_store = create_vector_store()
    embedding_service = create_embedding_service()
    
    settings = get_settings()
    if settings.rag_use_real_services:
        return RealSearchService(vector_store, embedding_service)
    return MockSearchService(vector_store, embedding_service)


def create_response_generator() -> ResponseGenerator:
    """Create response generator based on configuration."""
    settings = get_settings()
    if settings.rag_use_real_services:
        return LLMResponseGenerator()
    return MockResponseGenerator()


class RAGPipelineService(RAGPipeline):
    """Complete RAG pipeline implementation."""

    def __init__(
        self,
        document_processor: DocumentProcessor,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        search_service: SearchService,
        response_generator: ResponseGenerator,
    ):
        self.document_processor = document_processor
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.search_service = search_service
        self.response_generator = response_generator

    async def process_document(self, document_id: int, content: str) -> bool:
        """Process a document through the complete pipeline."""
        try:
            # Process document into chunks
            config = ProcessingConfig()
            chunks = await self.document_processor.process_document(
                document_id, content, config
            )

            # Generate embeddings for chunks
            texts = [chunk.content for chunk in chunks]
            embeddings = await self.embedding_service.generate_embeddings_batch(texts)

            # Attach embeddings to chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding

            # Store chunks in vector store
            success = await self.vector_store.store_chunks(chunks)
            return success

        except Exception as e:
            print(f"Error processing document {document_id}: {e}")
            return False

    async def query(self, search_query: SearchQuery) -> RAGResponse:
        """Query the RAG pipeline and return a response."""
        start_time = time.time()

        # Search for relevant chunks
        search_results = await self.search_service.search(search_query)

        # Generate response
        context_chunks = [result.chunk for result in search_results]
        answer = await self.response_generator.generate_response(
            search_query.query, context_chunks
        )

        processing_time = time.time() - start_time

        return RAGResponse(
            query=search_query.query,
            answer=answer,
            sources=search_results,
            processing_time=processing_time,
        )

    async def query_stream(
        self, search_query: SearchQuery
    ) -> AsyncGenerator[str, None]:
        """Query the RAG pipeline and return a streaming response."""
        # Search for relevant chunks
        search_results = await self.search_service.search(search_query)

        # Generate streaming response
        context_chunks = [result.chunk for result in search_results]
        async for chunk in self.response_generator.generate_response_stream(
            search_query.query, context_chunks
        ):
            yield chunk

    async def delete_document(self, document_id: int) -> bool:
        """Delete a document and all its chunks from the pipeline."""
        return await self.vector_store.delete_document_chunks(document_id)
