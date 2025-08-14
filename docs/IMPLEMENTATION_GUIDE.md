# RBAC-RAG Implementation Guide

## Executive Summary

This guide provides a complete roadmap for implementing a production-ready Role-Based Access Control (RBAC) integrated Retrieval Augmented Generation (RAG) system. The architecture is designed based on industry best practices and extensive research from leading implementations in the field.

## Project Structure Overview

```
rbac-rag-system/
├── backend/
│   ├── app/
│   │   ├── auth/              # Authentication & authorization
│   │   ├── documents/         # Document management
│   │   ├── rag/              # RAG pipeline
│   │   ├── security/         # Security services
│   │   ├── api/              # API endpoints
│   │   └── core/             # Core utilities
│   ├── tests/                # Test suites
│   ├── migrations/           # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API services
│   │   ├── hooks/            # Custom hooks
│   │   └── utils/            # Utilities
│   ├── public/
│   └── package.json
├── cerbos/
│   ├── policies/           # Cerbos policies
│   └── schemas/            # Cerbos schemas
├── docker/
│   ├── docker-compose.yml    # Development environment
│   ├── docker-compose.prod.yml  # Production environment
│   └── Dockerfile.*          # Individual service containers
├── scripts/
│   ├── setup.sh             # Environment setup
│   ├── deploy.sh            # Deployment script
│   └── migrate.sh           # Database migration
├── docs/
│   ├── api/                 # API documentation
│   ├── deployment/          # Deployment guides
│   └── security/            # Security documentation
└── README.md
```

## Technology Stack Recommendations

### Core Technologies
- **Backend Framework**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL 14+
- **Vector Database**: ChromaDB or Pinecone
- **Cache**: Redis 6+
- **Message Queue**: Celery with Redis
- **Web Server**: Uvicorn + Nginx
- **Containerization**: Docker + Docker Compose

### AI/ML Stack
- **Embeddings**: OpenAI Ada-002 or Sentence Transformers
- **LLM**: OpenAI GPT-4, Anthropic Claude, or local models (Llama 2)
- **Text Processing**: spaCy, NLTK
- **Vector Operations**: FAISS, NumPy

### Security & Monitoring
- **Authentication**: JWT with FastAPI-Users
- **Authorization**: Cerbos (Policy-as-Code)
- **Monitoring**: Prometheus + Grafana
- **Logging**: Structured logging with loguru
- **Security**: OWASP guidelines compliance

## Phase-by-Phase Implementation

### Phase 1: Foundation Setup (Weeks 1-2)

#### 1.1 Environment Setup
```bash
# Clone repository structure
mkdir rbac-rag-system && cd rbac-rag-system

# Set up Python virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install base dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary redis celery cerbos
```

#### 1.2 Database Schema Creation
```sql
-- Execute the complete database schema from auth-layer-design.md
-- and document-access-control.md

-- Key tables:
-- users, roles, user_roles, user_sessions
-- documents, document_access_control, document_chunks
-- access_audit_log, document_processing_jobs
```

#### 1.3 Basic API Structure
```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.router import auth_router
from app.documents.router import documents_router
from app.rag.router import rag_router

app = FastAPI(title="RBAC-RAG System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(documents_router, prefix="/api/documents", tags=["documents"])
app.include_router(rag_router, prefix="/api/rag", tags=["rag"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### Phase 2: Authentication & Authorization with Cerbos (Weeks 3-4)

#### 2.1 User Management Implementation
```python
# app/auth/services.py - Implementation from auth-layer-design.md
# Key components:
# - AuthService class with JWT handling
# - PasswordService for secure password management
# - Database models and operations
```

#### 2.2 Cerbos Integration
```python
# app/auth/cerbos_client.py
from cerbos.sdk.client import CerbosClient
from cerbos.sdk.model import Principal, Resource
from app.core.config import settings

# Initialize Cerbos client
cerbos_client = CerbosClient(host=settings.cerbos_url)

async def check_permission(principal: Principal, resource: Resource, action: str) -> bool:
    """Check permission with Cerbos."""
    return cerbos_client.is_allowed(action, principal, resource)
```

#### 2.3 RBAC Middleware
```python
# app/auth/middleware.py
from fastapi import Depends, HTTPException
from app.auth.cerbos_client import check_permission, Principal, Resource
from app.auth.services import get_current_user

# Example of a permission check in a middleware or endpoint
async def require_permission(resource_id: str, action: str, user: dict = Depends(get_current_user)):
    principal = Principal(
        id=user["id"],
        roles=user["roles"],
        attr=user["attributes"]
    )
    resource = Resource(
        id=resource_id,
        kind="document",
        attr={"owner": user["id"]} # Example attribute
    )
    
    allowed = await check_permission(principal, resource, action)
    if not allowed:
        raise HTTPException(status_code=403, detail="Permission denied")
```

### Phase 3: Document Management (Weeks 5-6)

#### 3.1 Document Processing Pipeline
```python
# app/documents/services.py
# Implementation from document-access-control.md:
# - DocumentIngestionService
# - AccessControlService  
# - DocumentLifecycleService
```

#### 3.2 File Upload and Processing
```python
# app/documents/router.py
from fastapi import UploadFile, File, Depends
from app.auth.middleware import require_permission

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    metadata: dict = None,
    current_user: dict = Depends(get_current_user)
):
    # Before processing, check if user has permission to create documents
    await require_permission(resource_id="new_document", action="create", user=current_user)
    
    # File validation, virus scanning, processing
    # Automatic classification and access control setup
    pass
```

### Phase 4: RAG Pipeline (Weeks 7-8)

#### 4.1 Core RAG Services
```python
# app/rag/services.py
# Complete implementation from rag-pipeline-design.md:
# - RAGPipelineService
# - SecurityFilterService (integrates with Cerbos)
# - ResponseCacheService
```

### Phase 5: ERP Integration (Weeks 9-10)

#### 5.1 ERP Connectors
- Implement database connectors for various ERP systems as detailed in `ERP-DATABASE-CONNECTORS.md`.
- Use a factory pattern to instantiate the correct connector based on the ERP system type.

```python
# app/erp/connectors.py
from app.erp.base_connector import BaseERPConnector
from app.erp.sap_connector import SAPConnector
from app.erp.oracle_connector import OracleConnector

class ERPConnectorFactory:
    @staticmethod
    def get_connector(erp_system: str) -> BaseERPConnector:
        if erp_system == "sap":
            return SAPConnector()
        elif erp_system == "oracle":
            return OracleConnector()
        else:
            raise ValueError("Unsupported ERP system")
```

#### 5.2 Data Synchronization
- Implement a data synchronization service to periodically pull data from the ERP system into the RAG system.
- Use Celery for asynchronous data synchronization tasks.

```python
# app/erp/sync_service.py
from app.erp.connectors import ERPConnectorFactory
from app.documents.services import DocumentIngestionService

async def sync_erp_data(erp_system: str):
    connector = ERPConnectorFactory.get_connector(erp_system)
    documents = await connector.fetch_documents()
    
    for doc in documents:
        await DocumentIngestionService.ingest_document(doc)
```

### Phase 6: Security & Testing (Weeks 11-12)

#### 6.1 Security Hardening
- Refer to `ERP-SECURITY-PATTERNS.md` for detailed security best practices.

#### 6.2 Comprehensive Testing
- Write unit and integration tests for all components, including Cerbos policy enforcement.

### Phase 7: Frontend Development (Weeks 13-14)
(Content remains the same)

### Phase 8: Deployment & Production (Weeks 15-16)

#### 8.1 Docker Configuration
```dockerfile
# docker/Dockerfile.backend
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker/docker-compose.prod.yml
version: '3.8'
services:
  backend:
    build:
      context: ../backend
      dockerfile: ../docker/Dockerfile.backend
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/rbac_rag
      - REDIS_URL=redis://redis:6379/0
      - CERBOS_URL=http://cerbos:3592
    depends_on:
      - postgres
      - redis
      - cerbos
  
  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=rbac_rag
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

  cerbos:
    image: ghcr.io/cerbos/cerbos:latest
    ports:
      - "3592:3592"
      - "3593:3593"
    volumes:
      - ../cerbos/policies:/policies
    command: ["server", "--config=/policies/config.yaml"]

volumes:
  postgres_data:
  redis_data:
```

## Configuration Management

### Environment Variables
```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost:5432/rbac_rag
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-super-secret-key-here
OPENAI_API_KEY=your-openai-api-key
CHROMADB_HOST=localhost
CHROMADB_PORT=8000
CERBOS_URL=http://localhost:3592

# Security settings
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
PASSWORD_MIN_LENGTH=8

# RAG settings
MAX_CONTEXT_TOKENS=4000
DEFAULT_TEMPERATURE=0.3
MAX_RESPONSE_TOKENS=1000
```

(The rest of the file remains the same)
