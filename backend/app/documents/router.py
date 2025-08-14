from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..auth.models import User
from ..cerbos.client import cerbos_client
from ..core.config import get_settings
from ..core.db import db_dependency
from .schemas import (
    DocumentCreate,
    DocumentListResponse,
    DocumentResponse,
    DocumentUpdate,
    DocumentUploadResponse,
)
from .service import document_service

security = HTTPBearer()
router = APIRouter(prefix="/documents", tags=["documents"])


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Extract user info from JWT token"""
    settings = get_settings()
    token = credentials.credentials
    try:
        data = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    username = data.get("sub")
    roles = data.get("roles", [])
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token subject")

    return {"username": username, "roles": roles}


@router.post("/", response_model=DocumentUploadResponse)
def create_document(
    document: DocumentCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(db_dependency),
):
    """Create a new document"""
    # Check authorization using Cerbos
    allowed = cerbos_client.authorize(
        current_user["roles"], resource="document", action="create"
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden by policy")

    # Get user ID from database
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create document
    document_data = document.model_dump()
    created_doc = document_service.create_document(db, document_data, user.id)

    return DocumentUploadResponse(
        id=created_doc.id,
        title=created_doc.title,
        message="Document created successfully",
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(db_dependency),
):
    """Get a document by ID"""
    # Check authorization
    allowed = cerbos_client.authorize(
        current_user["roles"], resource="document", action="view"
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden by policy")

    # Get user ID
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get document with access control
    document = document_service.get_document(
        db, document_id, user.id, current_user["roles"]
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.get("/", response_model=DocumentListResponse)
def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(db_dependency),
):
    """List documents with pagination"""
    # Check authorization
    allowed = cerbos_client.authorize(
        current_user["roles"], resource="document", action="list"
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden by policy")

    # Get user ID
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # List documents with access control
    documents, total = document_service.list_documents(
        db, user.id, current_user["roles"], page, per_page
    )

    return DocumentListResponse(
        documents=documents, total=total, page=page, per_page=per_page
    )


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(db_dependency),
):
    """Update a document"""
    # Check authorization
    allowed = cerbos_client.authorize(
        current_user["roles"], resource="document", action="update"
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden by policy")

    # Get user ID
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update document with access control
    update_data = {
        k: v for k, v in document_update.model_dump().items() if v is not None
    }
    updated_doc = document_service.update_document(
        db, document_id, update_data, user.id, current_user["roles"]
    )

    if not updated_doc:
        raise HTTPException(
            status_code=404, detail="Document not found or access denied"
        )

    return updated_doc


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(db_dependency),
):
    """Delete a document"""
    # Check authorization
    allowed = cerbos_client.authorize(
        current_user["roles"], resource="document", action="delete"
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden by policy")

    # Get user ID
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete document with access control
    success = document_service.delete_document(
        db, document_id, user.id, current_user["roles"]
    )

    if not success:
        raise HTTPException(
            status_code=404, detail="Document not found or access denied"
        )

    return {"message": "Document deleted successfully"}
