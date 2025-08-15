"""
RAG pipeline API router.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from ..documents.router import get_current_user
from ..documents.service import DocumentService
from .models import RAGResponse, SearchQuery
from .exceptions import RAGError
from .service import (
    RAGPipelineService,
    create_document_processor,
    create_embedding_service,
    create_response_generator,
    create_search_service,
    create_vector_store,
)

router = APIRouter(prefix="/rag", tags=["RAG"])

# Initialize RAG pipeline components using factory functions
document_processor = create_document_processor()
embedding_service = create_embedding_service()
vector_store = create_vector_store()
search_service = create_search_service()
response_generator = create_response_generator()

rag_pipeline = RAGPipelineService(
    document_processor=document_processor,
    embedding_service=embedding_service,
    vector_store=vector_store,
    search_service=search_service,
    response_generator=response_generator,
)


@router.post("/query", response_model=RAGResponse)
async def query_rag(
    search_query: SearchQuery, current_user: dict = Depends(get_current_user)
):
    """Query the RAG pipeline."""
    try:
        # Set user_id from current user
        search_query.user_id = current_user.get("id", 1)

        # Perform RAG query
        response = await rag_pipeline.query(search_query)
        return response

    except RAGError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"RAG processing error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing RAG query: {str(e)}",
        )


@router.post("/query/stream")
async def query_rag_stream(
    search_query: SearchQuery, current_user: dict = Depends(get_current_user)
):
    """Query the RAG pipeline with streaming response."""
    try:
        # Set user_id from current user
        search_query.user_id = current_user.get("id", 1)

        async def generate_stream():
            async for chunk in rag_pipeline.query_stream(search_query):
                yield chunk

        return StreamingResponse(generate_stream(), media_type="text/plain")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing streaming RAG query: {str(e)}",
        )


@router.post("/documents/{document_id}/process")
async def process_document(
    document_id: int,
    current_user: dict = Depends(get_current_user),
    document_service: DocumentService = Depends(),
):
    """Process a document through the RAG pipeline."""
    try:
        # Get document
        document = await document_service.get_document(document_id, current_user)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        # Process document through RAG pipeline
        success = await rag_pipeline.process_document(document_id, document.content)

        if success:
            return {"message": f"Document {document_id} processed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process document",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}",
        )


@router.delete("/documents/{document_id}")
async def delete_document_from_rag(
    document_id: int, current_user: dict = Depends(get_current_user)
):
    """Delete a document from the RAG pipeline."""
    try:
        success = await rag_pipeline.delete_document(document_id)

        if success:
            return {"message": f"Document {document_id} deleted from RAG pipeline"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document from RAG pipeline",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document from RAG pipeline: {str(e)}",
        )


@router.get("/stats")
async def get_rag_stats(current_user: dict = Depends(get_current_user)):
    """Get RAG pipeline statistics."""
    try:
        total_chunks = await vector_store.get_chunk_count()

        from ..core.config import get_settings
        settings = get_settings()
        
        return {
            "total_chunks": total_chunks,
            "vector_store_type": "faiss" if settings.rag_use_real_services else "mock",
            "embedding_service": settings.rag_embedding_model if settings.rag_use_real_services else "mock",
            "document_processor": "advanced" if settings.rag_use_real_services else "simple",
            "use_real_services": settings.rag_use_real_services,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting RAG stats: {str(e)}",
        )
