"""
Custom exceptions for RAG pipeline components.
"""


class RAGError(Exception):
    """Base exception for RAG pipeline errors."""
    pass


class DocumentProcessingError(RAGError):
    """Raised when document processing fails."""
    pass


class EmbeddingError(RAGError):
    """Raised when embedding generation fails."""
    pass


class VectorStoreError(RAGError):
    """Raised when vector store operations fail."""
    pass


class SearchError(RAGError):
    """Raised when search operations fail."""
    pass


class ResponseGenerationError(RAGError):
    """Raised when response generation fails."""
    pass


class ConfigurationError(RAGError):
    """Raised when RAG configuration is invalid."""
    pass


class PersistenceError(RAGError):
    """Raised when persistence operations fail."""
    pass
