from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from .models import Document


class DocumentService:
    def __init__(self):
        pass

    def create_document(
        self, db: Session, document_data: dict, owner_id: int
    ) -> Document:
        """Create a new document"""
        document = Document(**document_data, owner_id=owner_id)
        db.add(document)
        db.commit()
        db.refresh(document)
        return document

    def get_document(
        self, db: Session, document_id: int, user_id: int, user_roles: List[str]
    ) -> Optional[Document]:
        """Get a document by ID with access control"""
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return None

        # Check access: owner can access, public documents can be accessed by anyone
        if document.owner_id == user_id or document.is_public:
            return document

        # Admin can access all documents
        if "admin" in user_roles:
            return document

        return None

    def list_documents(
        self,
        db: Session,
        user_id: int,
        user_roles: List[str],
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[List[Document], int]:
        """List documents with access control and pagination"""
        query = db.query(Document)

        # Filter by access: user's own documents + public documents
        if "admin" in user_roles:
            # Admin sees all documents
            pass
        else:
            query = query.filter(
                or_(Document.owner_id == user_id, Document.is_public == True)
            )

        total = query.count()
        documents = query.offset((page - 1) * per_page).limit(per_page).all()

        return documents, total

    def update_document(
        self,
        db: Session,
        document_id: int,
        update_data: dict,
        user_id: int,
        user_roles: List[str],
    ) -> Optional[Document]:
        """Update a document with access control"""
        document = self.get_document(db, document_id, user_id, user_roles)
        if not document:
            return None

        # Only owner or admin can update
        if document.owner_id != user_id and "admin" not in user_roles:
            return None

        for field, value in update_data.items():
            if value is not None and hasattr(document, field):
                setattr(document, field, value)

        db.commit()
        db.refresh(document)
        return document

    def delete_document(
        self, db: Session, document_id: int, user_id: int, user_roles: List[str]
    ) -> bool:
        """Delete a document with access control"""
        document = self.get_document(db, document_id, user_id, user_roles)
        if not document:
            return False

        # Only owner or admin can delete
        if document.owner_id != user_id and "admin" not in user_roles:
            return False

        db.delete(document)
        db.commit()
        return True


document_service = DocumentService()
