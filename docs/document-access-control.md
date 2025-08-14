# Document Access Control System Design

## Overview
This document outlines the comprehensive design for document access control in the RBAC-RAG system, ensuring secure document ingestion, classification, and retrieval based on user roles and permissions.

## Document Classification Framework

### 1. Classification Levels

```python
CLASSIFICATION_LEVELS = {
    "public": {
        "level": 0,
        "description": "Information that can be freely shared",
        "required_clearance": ["*"],
        "retention_policy": "indefinite",
        "examples": ["company blog posts", "public announcements", "marketing materials"]
    },
    "internal": {
        "level": 1,
        "description": "Information for internal company use",
        "required_clearance": ["employee", "manager", "admin"],
        "retention_policy": "7_years",
        "examples": ["internal policies", "meeting notes", "project updates"]
    },
    "confidential": {
        "level": 2,
        "description": "Sensitive business information",
        "required_clearance": ["manager", "admin"],
        "retention_policy": "10_years",
        "examples": ["financial reports", "strategic plans", "customer data"]
    },
    "restricted": {
        "level": 3,
        "description": "Highly sensitive information",
        "required_clearance": ["admin"],
        "retention_policy": "permanent",
        "examples": ["legal documents", "personnel records", "trade secrets"]
    }
}

DEPARTMENT_ACCESS = {
    "hr": {
        "documents": ["employee_records", "policies", "training_materials"],
        "cross_access": ["legal", "finance"],  # Can access some legal/finance docs
        "restricted_from": ["engineering", "sales"]
    },
    "finance": {
        "documents": ["financial_reports", "budgets", "contracts"],
        "cross_access": ["hr", "legal"],
        "restricted_from": ["engineering"]
    },
    "engineering": {
        "documents": ["technical_specs", "code_documentation", "architecture"],
        "cross_access": ["product"],
        "restricted_from": ["finance", "hr"]
    },
    "legal": {
        "documents": ["contracts", "compliance", "litigation"],
        "cross_access": ["hr", "finance"],
        "restricted_from": ["engineering", "sales"]
    },
    "sales": {
        "documents": ["customer_data", "proposals", "pricing"],
        "cross_access": ["marketing"],
        "restricted_from": ["hr", "engineering"]
    }
}
```

### 2. Document Metadata Schema

```sql
-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    file_name VARCHAR(255),
    file_path TEXT,
    file_size BIGINT,
    file_type VARCHAR(50),
    content_hash VARCHAR(64),
    classification_level VARCHAR(20) NOT NULL,
    department VARCHAR(50),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    tags TEXT[],
    source_url TEXT,
    language VARCHAR(10) DEFAULT 'en'
);

-- Document access control
CREATE TABLE document_access_control (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    access_type VARCHAR(20) NOT NULL, -- 'role', 'user', 'department'
    access_value VARCHAR(100) NOT NULL, -- role name, user id, or department
    permission_type VARCHAR(20) NOT NULL, -- 'read', 'write', 'admin'
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Document chunks for vector storage
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_metadata JSONB,
    embedding_id VARCHAR(255), -- Reference to vector database
    created_at TIMESTAMP DEFAULT NOW()
);

-- Document processing jobs
CREATE TABLE document_processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL, -- 'ingestion', 'classification', 'embedding'
    status VARCHAR(20) NOT NULL, -- 'pending', 'processing', 'completed', 'failed'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    job_data JSONB
);
```

### 3. Document Ingestion Pipeline

```python
from typing import List, Optional, Dict, Any
import asyncio
from pathlib import Path
import hashlib
from datetime import datetime, timedelta

class DocumentIngestionService:
    def __init__(self, 
                 classification_service,
                 embedding_service,
                 vector_db_service,
                 access_control_service):
        self.classifier = classification_service
        self.embedder = embedding_service
        self.vector_db = vector_db_service
        self.access_control = access_control_service
        
    async def ingest_document(self, 
                            file_path: str, 
                            user_id: str,
                            metadata: Optional[Dict[str, Any]] = None) -> str:
        """Main document ingestion workflow"""
        
        # Step 1: File validation and preprocessing
        document_data = await self._preprocess_file(file_path, user_id)
        
        # Step 2: Content extraction
        content = await self._extract_content(file_path, document_data['file_type'])
        
        # Step 3: Automatic classification
        classification = await self._classify_document(content, metadata)
        
        # Step 4: Create document record
        document_id = await self._create_document_record(
            document_data, classification, content, user_id
        )
        
        # Step 5: Text chunking
        chunks = await self._chunk_text(content, document_id)
        
        # Step 6: Generate embeddings
        await self._generate_embeddings(chunks, document_id)
        
        # Step 7: Set up access control
        await self._setup_access_control(document_id, classification, user_id)
        
        # Step 8: Index in vector database
        await self._index_in_vector_db(chunks, classification)
        
        return document_id
    
    async def _preprocess_file(self, file_path: str, user_id: str) -> Dict[str, Any]:
        """Validate and preprocess uploaded file"""
        file_path = Path(file_path)
        
        # File validation
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = file_path.stat().st_size
        max_size = 100 * 1024 * 1024  # 100MB limit
        
        if file_size > max_size:
            raise ValueError(f"File too large: {file_size} bytes (max: {max_size})")
        
        # Calculate file hash for deduplication
        content_hash = await self._calculate_file_hash(file_path)
        
        # Check for duplicates
        existing_doc = await self._find_duplicate_document(content_hash)
        if existing_doc:
            raise ValueError(f"Duplicate document found: {existing_doc['id']}")
        
        return {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "file_size": file_size,
            "file_type": file_path.suffix.lower(),
            "content_hash": content_hash
        }
    
    async def _classify_document(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Automatically classify document based on content and metadata"""
        
        # Rule-based classification
        classification = await self._rule_based_classification(content, metadata)
        
        # ML-based classification (if available)
        if self.classifier.has_ml_model():
            ml_classification = await self.classifier.classify_with_ml(content)
            classification = self._merge_classifications(classification, ml_classification)
        
        # Manual override if specified in metadata
        if metadata and 'classification_override' in metadata:
            classification['level'] = metadata['classification_override']
            classification['manual_override'] = True
        
        return classification
    
    async def _rule_based_classification(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based document classification"""
        
        content_lower = content.lower()
        
        # Financial keywords
        financial_keywords = [
            'revenue', 'profit', 'budget', 'financial', 'earnings', 
            'balance sheet', 'income statement', 'cash flow'
        ]
        
        # HR keywords
        hr_keywords = [
            'salary', 'employee', 'personnel', 'hiring', 'termination',
            'performance review', 'benefits', 'vacation'
        ]
        
        # Legal keywords
        legal_keywords = [
            'contract', 'agreement', 'litigation', 'compliance',
            'regulation', 'legal', 'attorney', 'lawsuit'
        ]
        
        # Confidential indicators
        confidential_keywords = [
            'confidential', 'proprietary', 'trade secret', 'sensitive',
            'internal only', 'restricted', 'classified'
        ]
        
        # Determine classification
        classification = {
            'level': 'internal',  # default
            'department': 'general',
            'tags': [],
            'confidence': 0.5
        }
        
        # Check for explicit confidentiality markers
        if any(keyword in content_lower for keyword in confidential_keywords):
            classification['level'] = 'confidential'
            classification['confidence'] = 0.9
        
        # Department-specific classification
        if any(keyword in content_lower for keyword in financial_keywords):
            classification['department'] = 'finance'
            classification['tags'].append('financial')
            if classification['level'] == 'internal':
                classification['level'] = 'confidential'
        
        elif any(keyword in content_lower for keyword in hr_keywords):
            classification['department'] = 'hr'
            classification['tags'].append('hr')
            classification['level'] = 'confidential'  # HR docs are typically confidential
        
        elif any(keyword in content_lower for keyword in legal_keywords):
            classification['department'] = 'legal'
            classification['tags'].append('legal')
            classification['level'] = 'restricted'  # Legal docs are typically restricted
        
        # Check metadata for additional context
        if metadata:
            if 'source_department' in metadata:
                classification['department'] = metadata['source_department']
            
            if 'document_type' in metadata:
                doc_type = metadata['document_type'].lower()
                if doc_type in ['contract', 'legal_document']:
                    classification['level'] = 'restricted'
                elif doc_type in ['financial_report', 'budget']:
                    classification['level'] = 'confidential'
        
        return classification

class AccessControlService:
    def __init__(self, db_service):
        self.db = db_service
    
    async def setup_document_access(self, document_id: str, classification: Dict[str, Any], created_by: str):
        """Set up access control rules for a document"""
        
        access_rules = []
        
        # Creator always gets admin access
        access_rules.append({
            'document_id': document_id,
            'access_type': 'user',
            'access_value': created_by,
            'permission_type': 'admin',
            'granted_by': created_by
        })
        
        # Classification-based access
        classification_level = classification['level']
        required_clearance = CLASSIFICATION_LEVELS[classification_level]['required_clearance']
        
        for clearance in required_clearance:
            if clearance == '*':
                # Public access - no specific rule needed
                continue
            
            access_rules.append({
                'document_id': document_id,
                'access_type': 'role',
                'access_value': clearance,
                'permission_type': 'read',
                'granted_by': created_by
            })
        
        # Department-based access
        department = classification.get('department')
        if department and department != 'general':
            access_rules.append({
                'document_id': document_id,
                'access_type': 'department',
                'access_value': department,
                'permission_type': 'read',
                'granted_by': created_by
            })
            
            # Cross-department access
            dept_config = DEPARTMENT_ACCESS.get(department, {})
            for cross_dept in dept_config.get('cross_access', []):
                access_rules.append({
                    'document_id': document_id,
                    'access_type': 'department',
                    'access_value': cross_dept,
                    'permission_type': 'read',
                    'granted_by': created_by
                })
        
        # Insert access rules
        await self.db.insert_document_access_rules(access_rules)
    
    async def check_document_access(self, document_id: str, user_id: str, 
                                  user_roles: List[str], user_department: str, 
                                  permission_type: str = 'read') -> bool:
        """Check if user has access to document"""
        
        # Get document classification
        document = await self.db.get_document(document_id)
        if not document:
            return False
        
        # Document creator always has access
        if document['created_by'] == user_id:
            return True
        
        # Check classification-level access
        classification_level = document['classification_level']
        required_clearance = CLASSIFICATION_LEVELS[classification_level]['required_clearance']
        
        # Admin role bypasses all restrictions
        if 'admin' in user_roles:
            return True
        
        # Check if user has required clearance level
        if '*' not in required_clearance and not any(role in user_roles for role in required_clearance):
            return False
        
        # Get specific access control rules
        access_rules = await self.db.get_document_access_rules(document_id)
        
        # Check user-specific access
        user_access = [rule for rule in access_rules 
                      if rule['access_type'] == 'user' and rule['access_value'] == user_id]
        if user_access and any(rule['permission_type'] == permission_type or rule['permission_type'] == 'admin' 
                              for rule in user_access):
            return True
        
        # Check role-based access
        role_access = [rule for rule in access_rules 
                      if rule['access_type'] == 'role' and rule['access_value'] in user_roles]
        if role_access and any(rule['permission_type'] == permission_type or rule['permission_type'] == 'admin' 
                              for rule in role_access):
            return True
        
        # Check department-based access
        dept_access = [rule for rule in access_rules 
                      if rule['access_type'] == 'department' and rule['access_value'] == user_department]
        if dept_access and any(rule['permission_type'] == permission_type or rule['permission_type'] == 'admin' 
                              for rule in dept_access):
            return True
        
        return False
```

### 4. Vector Database Integration with Access Control

```python
class VectorDatabaseService:
    def __init__(self, chromadb_client, access_control_service):
        self.client = chromadb_client
        self.access_control = access_control_service
        self.collection_name = "rbac_documents"
    
    async def index_document_chunks(self, chunks: List[Dict], classification: Dict[str, Any]):
        """Index document chunks with access control metadata"""
        
        collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Prepare data for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            documents.append(chunk['content'])
            
            # Embed access control information in metadata
            metadata = {
                'document_id': chunk['document_id'],
                'chunk_index': chunk['chunk_index'],
                'classification_level': classification['level'],
                'department': classification.get('department', 'general'),
                'tags': classification.get('tags', []),
                'created_at': chunk.get('created_at', datetime.utcnow().isoformat()),
                'source_type': chunk.get('source_type', 'document')
            }
            
            metadatas.append(metadata)
            ids.append(chunk['id'])
        
        # Add to vector database
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    async def search_with_access_control(self, 
                                       query: str, 
                                       user_id: str,
                                       user_roles: List[str], 
                                       user_department: str,
                                       limit: int = 10) -> List[Dict]:
        """Search documents with access control filtering"""
        
        collection = self.client.get_collection(self.collection_name)
        
        # Perform initial vector search
        results = collection.query(
            query_texts=[query],
            n_results=limit * 3,  # Get more results to account for filtering
            include=['metadatas', 'documents', 'distances']
        )
        
        # Filter results based on access control
        filtered_results = []
        
        for i, metadata in enumerate(results['metadatas'][0]):
            document_id = metadata['document_id']
            
            # Check if user has access to this document
            has_access = await self.access_control.check_document_access(
                document_id, user_id, user_roles, user_department
            )
            
            if has_access:
                filtered_results.append({
                    'document_id': document_id,
                    'content': results['documents'][0][i],
                    'metadata': metadata,
                    'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'chunk_index': metadata['chunk_index']
                })
            
            if len(filtered_results) >= limit:
                break
        
        return filtered_results
    
    async def advanced_search_with_filters(self,
                                         query: str,
                                         user_id: str,
                                         user_roles: List[str],
                                         user_department: str,
                                         filters: Optional[Dict[str, Any]] = None,
                                         limit: int = 10) -> List[Dict]:
        """Advanced search with additional filters"""
        
        # Build where clause for ChromaDB
        where_conditions = {}
        
        # Add access control filters
        accessible_levels = []
        for level, config in CLASSIFICATION_LEVELS.items():
            required_clearance = config['required_clearance']
            if ('*' in required_clearance or 
                any(role in user_roles for role in required_clearance)):
                accessible_levels.append(level)
        
        if accessible_levels:
            where_conditions['classification_level'] = {"$in": accessible_levels}
        
        # Add user-specified filters
        if filters:
            if 'department' in filters:
                where_conditions['department'] = filters['department']
            
            if 'tags' in filters:
                where_conditions['tags'] = {"$in": filters['tags']}
            
            if 'date_range' in filters:
                date_range = filters['date_range']
                if 'start' in date_range:
                    where_conditions['created_at'] = {"$gte": date_range['start']}
                if 'end' in date_range:
                    if 'created_at' not in where_conditions:
                        where_conditions['created_at'] = {}
                    where_conditions['created_at']['$lte'] = date_range['end']
        
        collection = self.client.get_collection(self.collection_name)
        
        # Perform search with filters
        results = collection.query(
            query_texts=[query],
            where=where_conditions,
            n_results=limit,
            include=['metadatas', 'documents', 'distances']
        )
        
        # Additional access control verification
        verified_results = []
        for i, metadata in enumerate(results['metadatas'][0]):
            document_id = metadata['document_id']
            
            has_access = await self.access_control.check_document_access(
                document_id, user_id, user_roles, user_department
            )
            
            if has_access:
                verified_results.append({
                    'document_id': document_id,
                    'content': results['documents'][0][i],
                    'metadata': metadata,
                    'similarity_score': 1 - results['distances'][0][i],
                    'chunk_index': metadata['chunk_index']
                })
        
        return verified_results
```

### 5. Document Lifecycle Management

```python
class DocumentLifecycleService:
    def __init__(self, db_service, vector_db_service, storage_service):
        self.db = db_service
        self.vector_db = vector_db_service
        self.storage = storage_service
    
    async def update_document_classification(self, document_id: str, 
                                           new_classification: str, 
                                           updated_by: str) -> bool:
        """Update document classification and propagate changes"""
        
        # Verify user has permission to update classification
        if not await self._can_update_classification(document_id, updated_by):
            raise PermissionError("Insufficient permissions to update classification")
        
        # Update database record
        await self.db.update_document_classification(document_id, new_classification, updated_by)
        
        # Update vector database metadata
        await self.vector_db.update_document_metadata(document_id, {
            'classification_level': new_classification
        })
        
        # Update access control rules
        await self._refresh_access_control_rules(document_id, new_classification, updated_by)
        
        # Log the change
        await self._log_classification_change(document_id, new_classification, updated_by)
        
        return True
    
    async def expire_document(self, document_id: str) -> bool:
        """Mark document as expired and remove from active search"""
        
        # Update database
        await self.db.expire_document(document_id)
        
        # Remove from vector database
        await self.vector_db.delete_document_chunks(document_id)
        
        # Move file to archive storage
        await self.storage.archive_document(document_id)
        
        return True
    
    async def delete_document(self, document_id: str, deleted_by: str) -> bool:
        """Permanently delete document and all associated data"""
        
        # Verify permissions
        if not await self._can_delete_document(document_id, deleted_by):
            raise PermissionError("Insufficient permissions to delete document")
        
        # Remove from vector database
        await self.vector_db.delete_document_chunks(document_id)
        
        # Remove from file storage
        await self.storage.delete_document_file(document_id)
        
        # Remove from database (cascades to chunks and access control)
        await self.db.delete_document(document_id)
        
        # Log deletion
        await self._log_document_deletion(document_id, deleted_by)
        
        return True
```

## Access Control Audit and Monitoring

### 1. Audit Logging

```sql
-- Audit log table
CREATE TABLE access_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL, -- 'document_access', 'search_query', 'classification_change'
    resource_type VARCHAR(50) NOT NULL, -- 'document', 'search_results'
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    success BOOLEAN NOT NULL
);
```

### 2. Access Monitoring

```python
class AccessMonitoringService:
    def __init__(self, db_service):
        self.db = db_service
    
    async def log_document_access(self, user_id: str, document_id: str, 
                                action: str, success: bool, 
                                ip_address: str = None, user_agent: str = None):
        """Log document access attempt"""
        
        await self.db.insert_audit_log({
            'user_id': user_id,
            'action': action,
            'resource_type': 'document',
            'resource_id': document_id,
            'success': success,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': datetime.utcnow()
        })
    
    async def generate_access_report(self, start_date: datetime, 
                                   end_date: datetime) -> Dict[str, Any]:
        """Generate access control audit report"""
        
        # Get access statistics
        total_accesses = await self.db.count_access_attempts(start_date, end_date)
        failed_accesses = await self.db.count_failed_access_attempts(start_date, end_date)
        
        # Top accessed documents
        top_documents = await self.db.get_top_accessed_documents(start_date, end_date, limit=10)
        
        # Users with most access attempts
        top_users = await self.db.get_top_accessing_users(start_date, end_date, limit=10)
        
        # Suspicious activity detection
        suspicious_activities = await self._detect_suspicious_activities(start_date, end_date)
        
        return {
            'period': {'start': start_date, 'end': end_date},
            'statistics': {
                'total_access_attempts': total_accesses,
                'failed_access_attempts': failed_accesses,
                'success_rate': (total_accesses - failed_accesses) / total_accesses if total_accesses > 0 else 0
            },
            'top_documents': top_documents,
            'top_users': top_users,
            'suspicious_activities': suspicious_activities
        }
```

This document access control system provides comprehensive security, flexibility, and auditability for the RBAC-RAG system while maintaining performance and usability.