# RBAC-RAG for ERP

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/React-18.2+-61DAFB.svg" alt="React">
  <img src="https://img.shields.io/badge/FastAPI-0.109+-009688.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</p>

A secure and scalable ERP system with Retrieval Augmented Generation (RAG) and Role-Based Access Control (RBAC). Built with FastAPI, React, PostgreSQL, and Cerbos policy engine.

## 🌟 Features

- **Authentication & Authorization**
  - JWT-based authentication with refresh tokens
  - Role-based access control (RBAC) via Cerbos policy engine
  - User role management (Admin, Manager, Employee, Guest)

- **Document Management**
  - CRUD operations for documents
  - Document metadata with access permissions
  - PostgreSQL for persistent storage

- **RAG (Retrieval-Augmented Generation)**
  - Local embeddings using Sentence Transformers
  - FAISS vector database for similarity search
  - Role-based document filtering at query time

- **Full-Stack Implementation**
  - FastAPI backend with async support
  - React 18 + TypeScript frontend
  - Docker & Docker Compose deployment

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                       │
│  React + TypeScript + React Router                              │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP REST API
┌────────────────────────────▼────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
│  ┌──────────┐  ┌─────────────┐  ┌─────────┐  ┌─────────────┐   │
│  │   Auth   │  │  Documents  │  │   RAG   │  │   Cerbos    │   │
│  │ JWT/OAuth2│  │   (CRUD)    │  │ Engine  │  │  (RBAC)     │   │
│  └──────────┘  └─────────────┘  └─────────┘  └─────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  PostgreSQL    │  │   Cerbos      │  │    Redis      │
│  (Metadata)   │  │  (Policies)   │  │    (Cache)    │
└───────────────┘  └───────────────┘  └───────────────┘
        │
        ▼
┌───────────────┐  ┌───────────────┐
│    FAISS      │  │   Sentence    │
│ (Vector Store)│◄─│  Transformers │
└───────────────┘  └───────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+
- Node.js 18+

### Running with Docker Compose

```bash
# Clone the repository
git clone https://github.com/uai-product/usmarter-ai.git
cd usmarter-ai

# Start all services
docker-compose -f docker/docker-compose.yml up
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Cerbos Policy Server**: http://localhost:3592

### Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run the server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## 📁 Project Structure

```
RBAC-RAG/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── auth/           # Authentication module
│   │   ├── documents/     # Document management
│   │   ├── rag/           # RAG engine
│   │   ├── cerbos/        # Authorization client
│   │   └── core/          # Core config & DB
│   ├── alembic/           # Database migrations
│   └── requirements.txt
│
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── contexts/      # Auth context
│   │   ├── hooks/         # Custom hooks
│   │   └── services/      # API services
│   └── package.json
│
├── cerbos/                 # RBAC policies
│   └── policies/
│
├── docker/                 # Docker configs
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── scripts/                # Utility scripts
│   ├── setup.sh
│   ├── deploy.sh
│   ├── migrate.sh
│   └── e2e-test.sh
│
└── docs/                   # Documentation
```

## 🔐 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login (get JWT token)
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout (revoke token)

### Documents
- `GET /documents` - List documents (RBAC filtered)
- `POST /documents` - Create document
- `GET /documents/{id}` - Get document by ID
- `PUT /documents/{id}` - Update document
- `DELETE /documents/{id}` - Delete document

### RAG Query
- `POST /rag/query` - Query with RAG (role-filtered)

### Health
- `GET /health` - System health check

## 🔧 Configuration

### Environment Variables (Backend)

```env
APP_ENV=dev
APP_DEBUG=true
APP_SECRET_KEY=your-secret-key
APP_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rbac_rag
APP_CERBOS_HOST=localhost:3593
```

### RBAC Roles

| Role | Description |
|------|-------------|
| `admin` | Full access to all resources |
| `manager` | Access to department documents |
| `employee` | Access to shared documents |
| `guest` | Read-only access to public documents |

## 🧪 Testing

```bash
# Backend tests
cd backend && python -m pytest

# Frontend tests
cd frontend && npm test

# End-to-end tests
./scripts/e2e-test.sh
```

## 📝 Code Quality

### Backend (Python)
```bash
cd backend
ruff check .          # Lint
black .              # Format
./scripts/lint.sh    # Both
```

### Frontend (React/TypeScript)
```bash
cd frontend
npm run lint         # Lint
npm run format      # Format
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, Python 3.12+ |
| Frontend | React 18, TypeScript |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy + Alembic |
| Auth | JWT (python-jose), bcrypt |
| Authorization | Cerbos (policy engine) |
| Vector Store | FAISS CPU |
| Embeddings | Sentence Transformers |
| Container | Docker + Docker Compose |
| Linting | Ruff, Black, ESLint, Prettier |

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 📚 Documentation

See the `docs/` directory for detailed documentation:
- [Architecture](docs/ARCHITECTURE.md)
- [Implementation Guide](docs/IMPLEMENTATION_GUIDE.md)
- [Cerbos Integration](docs/CERBOS-INTEGRATION-GUIDE.md)