# TODO

Feature-by-feature task tracker for RBAC-RAG (Gemini-led).

## Backlog

- [ ] Docs: Add migration guide to README

## In Progress

- [ ] RAG query interface implementation

## Done

- [x] CI and basic backend test harness
- [x] Backend: configuration/settings module (env-driven)
- [x] Backend: Cerbos client integration (stub with health check)
- [x] Docker Compose: add Postgres, Redis, Cerbos services; wire env
- [x] Backend: auth skeleton (JWT, users model, login/refresh endpoints)
- [x] Backend: RBAC with Cerbos
- [x] Backend: Password Verification & Refresh Tokens
- [x] Backend: Finalize Cerbos Integration
- [x] Backend: Database Migrations (Alembic)
- [x] Backend: Revoke Refresh Token Endpoint
- [x] Backend: Document Management Skeleton (Models, API, Cerbos Policy)
- [x] Backend: Create database migration for Document model
- [x] Backend: Align Cerbos policy with business logic for document deletion
- [x] Backend: Apply database migration for Document model
- [x] Backend: RAG pipeline skeleton (interfaces only)
- [x] Frontend: bootstrap app shell and health page
- [x] Tooling: lint/format (ruff/black; eslint/prettier)
- [x] E2E smoke test via docker-compose (API + frontend up)
- [x] Docs: Add migration guide to README
- [x] Docker: Fix frontend container stability
- [x] Backend: Real RAG implementations with sentence-transformers and FAISS
- [x] Frontend: Authentication and document management integration
