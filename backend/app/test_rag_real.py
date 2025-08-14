"""
Tests for real RAG implementations.
"""

import pytest
from unittest.mock import patch, AsyncMock

from .rag.models import SearchQuery, ProcessingConfig
from .rag.real_services import (
    AdvancedDocumentProcessor,
    FAISSVectorStore,
    LLMResponseGenerator,
    RealSearchService,
    SentenceTransformerEmbeddingService,
)


class TestAdvancedDocumentProcessor:
    """Test advanced document processor."""

    @pytest.fixture
    def processor(self):
        return AdvancedDocumentProcessor()

    @pytest.fixture
    def config(self):
        return ProcessingConfig(
            chunk_size=100,
            chunk_overlap=20,
            max_chunks_per_document=10
        )

    @pytest.mark.asyncio
    async def test_chunk_text_simple(self, processor, config):
        """Test simple text chunking."""
        text = "This is a simple text that should be chunked."
        chunks = await processor.chunk_text(text, config)
        
        assert len(chunks) == 1
        assert chunks[0] == text

    @pytest.mark.asyncio
    async def test_chunk_text_long(self, processor, config):
        """Test long text chunking."""
        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
        chunks = await processor.chunk_text(text, config)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= config.chunk_size for chunk in chunks)

    @pytest.mark.asyncio
    async def test_process_document(self, processor, config):
        """Test document processing."""
        content = "This is document content. It has multiple sentences."
        chunks = await processor.process_document(1, content, config)
        
        assert len(chunks) > 0
        assert all(chunk.document_id == 1 for chunk in chunks)
        assert all(chunk.metadata for chunk in chunks)


class TestFAISSVectorStore:
    """Test FAISS vector store."""

    @pytest.fixture
    def vector_store(self):
        return FAISSVectorStore(dimensions=384)

    @pytest.fixture
    def mock_chunks(self):
        from .rag.models import DocumentChunk
        return [
            DocumentChunk(
                id="chunk1",
                document_id=1,
                content="Test content 1",
                chunk_index=0,
                embedding=[0.1] * 384
            ),
            DocumentChunk(
                id="chunk2", 
                document_id=1,
                content="Test content 2",
                chunk_index=1,
                embedding=[0.2] * 384
            )
        ]

    @pytest.mark.asyncio
    async def test_store_chunks(self, vector_store, mock_chunks):
        """Test storing chunks."""
        success = await vector_store.store_chunks(mock_chunks)
        assert success is True
        assert len(vector_store.chunks) == 2

    @pytest.mark.asyncio
    async def test_search_similar(self, vector_store, mock_chunks):
        """Test similarity search."""
        # Store chunks first
        await vector_store.store_chunks(mock_chunks)
        
        # Search with query embedding
        query_embedding = [0.15] * 384
        results = await vector_store.search_similar(query_embedding, limit=2)
        
        assert len(results) > 0
        assert all(hasattr(result, 'similarity_score') for result in results)

    @pytest.mark.asyncio
    async def test_delete_document_chunks(self, vector_store, mock_chunks):
        """Test deleting document chunks."""
        # Store chunks first
        await vector_store.store_chunks(mock_chunks)
        assert len(vector_store.chunks) == 2
        
        # Delete chunks
        success = await vector_store.delete_document_chunks(1)
        assert success is True
        assert len(vector_store.chunks) == 0


class TestLLMResponseGenerator:
    """Test LLM response generator."""

    @pytest.fixture
    def generator(self):
        return LLMResponseGenerator()

    @pytest.fixture
    def mock_chunks(self):
        from .rag.models import DocumentChunk
        return [
            DocumentChunk(
                id="chunk1",
                document_id=1,
                content="This is test content for response generation.",
                chunk_index=0
            )
        ]

    @pytest.mark.asyncio
    async def test_generate_response(self, generator, mock_chunks):
        """Test response generation."""
        query = "What is the test content?"
        response = await generator.generate_response(query, mock_chunks)
        
        assert response is not None
        assert len(response) > 0
        assert query in response

    @pytest.mark.asyncio
    async def test_generate_response_empty_context(self, generator):
        """Test response generation with empty context."""
        query = "What is the test content?"
        response = await generator.generate_response(query, [])
        
        assert "don't have enough information" in response.lower()

    @pytest.mark.asyncio
    async def test_generate_response_stream(self, generator, mock_chunks):
        """Test streaming response generation."""
        query = "What is the test content?"
        chunks = []
        
        async for chunk in generator.generate_response_stream(query, mock_chunks):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert all(len(chunk) > 0 for chunk in chunks)


class TestRealSearchService:
    """Test real search service."""

    @pytest.fixture
    def mock_vector_store(self):
        store = FAISSVectorStore(dimensions=384)
        return store

    @pytest.fixture
    def mock_embedding_service(self):
        service = SentenceTransformerEmbeddingService()
        return service

    @pytest.fixture
    def search_service(self, mock_vector_store, mock_embedding_service):
        return RealSearchService(mock_vector_store, mock_embedding_service)

    @pytest.mark.asyncio
    async def test_search(self, search_service):
        """Test basic search functionality."""
        query = SearchQuery(
            query="test query",
            max_results=5,
            filters={}
        )
        
        results = await search_service.search(query)
        # Should return empty results if no documents are stored
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_with_reranking(self, search_service):
        """Test search with reranking."""
        query = SearchQuery(
            query="test query",
            max_results=5,
            filters={}
        )
        
        results = await search_service.search_with_reranking(query)
        assert isinstance(results, list)


class TestSentenceTransformerEmbeddingService:
    """Test sentence transformer embedding service."""

    @pytest.fixture
    def embedding_service(self):
        return SentenceTransformerEmbeddingService()

    @pytest.mark.asyncio
    async def test_generate_embedding(self, embedding_service):
        """Test single embedding generation."""
        text = "This is a test sentence."
        embedding = await embedding_service.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == embedding_service.dimensions
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, embedding_service):
        """Test batch embedding generation."""
        texts = ["First sentence.", "Second sentence.", "Third sentence."]
        embeddings = await embedding_service.generate_embeddings_batch(texts)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == len(texts)
        assert all(len(emb) == embedding_service.dimensions for emb in embeddings)

    @pytest.mark.asyncio
    async def test_get_config(self, embedding_service):
        """Test configuration retrieval."""
        config = await embedding_service.get_config()
        
        assert config.dimensions == embedding_service.dimensions
        assert config.model_name == embedding_service.model_name


class TestRAGIntegration:
    """Test integration between RAG components."""

    @pytest.mark.asyncio
    async def test_full_rag_pipeline(self):
        """Test complete RAG pipeline with real services."""
        from .rag.service import RAGPipelineService
        from .rag.real_services import (
            AdvancedDocumentProcessor,
            FAISSVectorStore,
            LLMResponseGenerator,
            RealSearchService,
            SentenceTransformerEmbeddingService,
        )
        
        # Create components
        processor = AdvancedDocumentProcessor()
        embedding_service = SentenceTransformerEmbeddingService()
        vector_store = FAISSVectorStore(embedding_service.dimensions)
        search_service = RealSearchService(vector_store, embedding_service)
        response_generator = LLMResponseGenerator()
        
        # Create pipeline
        pipeline = RAGPipelineService(
            document_processor=processor,
            embedding_service=embedding_service,
            vector_store=vector_store,
            search_service=search_service,
            response_generator=response_generator,
        )
        
        # Test document processing
        content = "This is a test document about artificial intelligence and machine learning."
        success = await pipeline.process_document(1, content)
        assert success is True
        
        # Test querying
        query = SearchQuery(
            query="What is artificial intelligence?",
            max_results=3,
            filters={}
        )
        
        response = await pipeline.query(query)
        assert response is not None
        assert response.query == query.query
        assert len(response.answer) > 0
