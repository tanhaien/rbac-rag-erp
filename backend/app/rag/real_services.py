"""
Real implementations of RAG pipeline components.
"""

import asyncio
import json
import os
from collections.abc import AsyncGenerator
from typing import Any, Dict, List, Optional
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from .interfaces import (
    DocumentProcessor,
    EmbeddingService,
    ResponseGenerator,
    SearchService,
    VectorStore,
)
from .models import (
    DocumentChunk,
    EmbeddingConfig,
    ProcessingConfig,
    SearchQuery,
    SearchResult,
)


class SentenceTransformerEmbeddingService(EmbeddingService):
    """Real embedding service using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimensions = self.model.get_sentence_embedding_dimension()
        self.config = EmbeddingConfig(dimensions=self.dimensions)

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, self.model.encode, text
        )
        return embedding.tolist()

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts in batch."""
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, self.model.encode, texts
        )
        return embeddings.tolist()

    async def get_config(self) -> EmbeddingConfig:
        """Get embedding service configuration."""
        return self.config


class FAISSVectorStore(VectorStore):
    """Real vector store using FAISS for similarity search."""

    def __init__(self, dimensions: int = 384, index_path: Optional[str] = None):
        self.dimensions = dimensions
        self.index_path = index_path
        self.chunks: Dict[str, DocumentChunk] = {}
        self.chunk_ids: List[str] = []
        
        if self.index_path and os.path.exists(self.index_path):
            print(f"Loading FAISS index from {self.index_path}")
            self.index = faiss.read_index(self.index_path)
            # We need to load chunks metadata separately
            meta_path = self.index_path + ".meta"
            if os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    meta_data = json.load(f)
                    self.chunks = {k: DocumentChunk(**v) for k, v in meta_data["chunks"].items()}
                    self.chunk_ids = meta_data["chunk_ids"]
        else:
            print("Creating new FAISS index")
            self.index = faiss.IndexFlatIP(dimensions)  # Inner product for cosine similarity
        
        self._index_built = self.index.ntotal > 0

    async def store_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """Store document chunks with their embeddings."""
        try:
            # Collect embeddings and chunk IDs
            embeddings = []
            chunk_ids = []
            
            for chunk in chunks:
                if chunk.embedding:
                    embeddings.append(chunk.embedding)
                    chunk_ids.append(chunk.id)
                    self.chunks[chunk.id] = chunk
            
            if embeddings:
                # Convert to numpy array and normalize for cosine similarity
                embeddings_array = np.array(embeddings, dtype=np.float32)
                faiss.normalize_L2(embeddings_array)
                
                # Add to FAISS index
                self.index.add(embeddings_array)
                self.chunk_ids.extend(chunk_ids)
                self._index_built = True
                await self._save_index()

            return True
        except Exception as e:
            print(f"Error storing chunks: {e}")
            return False

    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar chunks using vector similarity."""
        if not self._index_built or self.index.ntotal == 0:
            return []

        try:
            # Normalize query embedding
            query_array = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_array)

            # Search in FAISS
            scores, indices = self.index.search(query_array, min(limit * 2, self.index.ntotal))

            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx == -1:  # FAISS returns -1 for invalid indices
                    continue
                    
                chunk_id = self.chunk_ids[idx]
                chunk = self.chunks.get(chunk_id)
                
                if not chunk:
                    continue

                # Apply filters
                if filters:
                    if "document_id" in filters and chunk.document_id != filters["document_id"]:
                        continue

                results.append(SearchResult(
                    chunk=chunk,
                    similarity_score=float(score),
                    rank=len(results) + 1
                ))

                if len(results) >= limit:
                    break

            return results

        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []

    async def delete_document_chunks(self, document_id: int) -> bool:
        """Delete all chunks for a specific document."""
        try:
            # Find chunks to delete
            chunks_to_delete = []
            for chunk_id, chunk in self.chunks.items():
                if chunk.document_id == document_id:
                    chunks_to_delete.append(chunk_id)

            # Remove from storage
            for chunk_id in chunks_to_delete:
                del self.chunks[chunk_id]
                if chunk_id in self.chunk_ids:
                    self.chunk_ids.remove(chunk_id)

            # Rebuild index (FAISS doesn't support deletion, so we rebuild)
            if chunks_to_delete:
                await self._rebuild_index()
                await self._save_index()

            return True
        except Exception as e:
            print(f"Error deleting document chunks: {e}")
            return False

    async def get_chunk_count(self, document_id: Optional[int] = None) -> int:
        """Get total number of chunks, optionally filtered by document."""
        if document_id is None:
            return len(self.chunks)
        return len([c for c in self.chunks.values() if c.document_id == document_id])

    async def _save_index(self):
        """Save the FAISS index and metadata to disk."""
        if self.index_path:
            print(f"Saving FAISS index to {self.index_path}")
            faiss.write_index(self.index, self.index_path)
            meta_path = self.index_path + ".meta"
            with open(meta_path, "w") as f:
                # Need to convert DocumentChunk objects to dicts for JSON serialization
                chunks_dict = {k: v.dict() for k, v in self.chunks.items()}
                json.dump({"chunks": chunks_dict, "chunk_ids": self.chunk_ids}, f)

    async def _rebuild_index(self):
        """Rebuild FAISS index from stored chunks."""
        print("Rebuilding FAISS index...")
        new_index = faiss.IndexFlatIP(self.dimensions)
        
        if not self.chunks:
            self.index = new_index
            self.chunk_ids = []
            self._index_built = False
            return

        # Collect all embeddings
        embeddings = []
        chunk_ids = []
        
        for chunk_id, chunk in self.chunks.items():
            if chunk.embedding:
                embeddings.append(chunk.embedding)
                chunk_ids.append(chunk_id)

        if embeddings:
            embeddings_array = np.array(embeddings, dtype=np.float32)
            faiss.normalize_L2(embeddings_array)
            new_index.add(embeddings_array)
            
        self.index = new_index
        self.chunk_ids = chunk_ids
        self._index_built = True


class AdvancedDocumentProcessor(DocumentProcessor):
    """Advanced document processor with better text chunking."""

    async def process_document(
        self, document_id: int, content: str, config: ProcessingConfig
    ) -> List[DocumentChunk]:
        """Process a document and return chunks."""
        chunks = await self.chunk_text(content, config)

        document_chunks = []
        for i, chunk_content in enumerate(chunks):
            chunk = DocumentChunk(
                id=f"doc_{document_id}_chunk_{i}",
                document_id=document_id,
                content=chunk_content,
                chunk_index=i,
                metadata={
                    "chunk_size": len(chunk_content),
                    "word_count": len(chunk_content.split()),
                    "char_count": len(chunk_content)
                },
            )
            document_chunks.append(chunk)

        return document_chunks

    async def chunk_text(self, text: str, config: ProcessingConfig) -> List[str]:
        """Split text into chunks using advanced strategies."""
        if len(text) <= config.chunk_size:
            return [text]

        # Clean and normalize text
        text = self._clean_text(text)
        
        # Split into sentences first
        sentences = self._split_sentences(text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > config.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence

        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # Apply overlap if needed
        if config.chunk_overlap > 0 and len(chunks) > 1:
            chunks = self._apply_overlap(chunks, config.chunk_overlap)

        return chunks[:config.max_chunks_per_document]

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = " ".join(text.split())
        # Remove special characters that might interfere with chunking
        text = text.replace("\n", " ").replace("\r", " ")
        return text

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re
        
        # Simple sentence splitting - can be improved with NLP libraries
        sentence_endings = r'[.!?]+'
        sentences = re.split(sentence_endings, text)
        
        # Clean up sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences

    def _apply_overlap(self, chunks: List[str], overlap_size: int) -> List[str]:
        """Apply overlap between chunks."""
        if len(chunks) <= 1:
            return chunks

        overlapped_chunks = [chunks[0]]
        
        for i in range(1, len(chunks)):
            current_chunk = chunks[i]
            previous_chunk = chunks[i-1]
            
            # Find overlap point
            overlap_start = max(0, len(previous_chunk) - overlap_size)
            overlap_text = previous_chunk[overlap_start:]
            
            # Add overlap to current chunk if it doesn't already contain it
            if not current_chunk.startswith(overlap_text):
                current_chunk = overlap_text + " " + current_chunk
            
            overlapped_chunks.append(current_chunk)

        return overlapped_chunks


class LLMResponseGenerator(ResponseGenerator):
    """Response generator using a simple template-based approach."""

    async def generate_response(
        self, query: str, context_chunks: List[DocumentChunk]
    ) -> str:
        """Generate a response based on query and context chunks."""
        if not context_chunks:
            return "I don't have enough information to answer your question."

        # Combine context
        context_text = "\n\n".join([chunk.content for chunk in context_chunks])
        
        # Create a structured response
        response = f"""Based on the available information, here's what I found:

Query: {query}

Relevant Information:
{context_text[:2000]}...

Answer: Based on the provided context, I can help you with your question about "{query}". The information above contains relevant details that should address your query."""

        return response

    async def generate_response_stream(
        self, query: str, context_chunks: List[DocumentChunk]
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response."""
        response = await self.generate_response(query, context_chunks)
        
        # Stream the response word by word
        words = response.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.05)  # Faster than mock for better UX


class RealSearchService(SearchService):
    """Real search service implementation."""

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
        # Get initial results
        results = await self.search(query)
        
        # Simple reranking based on content relevance
        reranked_results = []
        for result in results:
            # Calculate simple relevance score based on query terms in content
            relevance_score = self._calculate_relevance(query.query, result.chunk.content)
            result.similarity_score = (result.similarity_score + relevance_score) / 2
            reranked_results.append(result)
        
        # Sort by new score
        return sorted(reranked_results, key=lambda x: x.similarity_score, reverse=True)

    def _calculate_relevance(self, query: str, content: str) -> float:
        """Calculate simple relevance score based on query terms."""
        query_terms = set(query.lower().split())
        content_terms = set(content.lower().split())
        
        if not query_terms:
            return 0.0
            
        intersection = query_terms.intersection(content_terms)
        return len(intersection) / len(query_terms)
