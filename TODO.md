# TODO

Feature-by-feature task tracker for RBAC-RAG (Gemini-led).

## Backlog

- [ ] Backend: RAG pipeline skeleton (interfaces only)
- [ ] Frontend: bootstrap app shell and health page
- [ ] Tooling: lint/format (ruff/black; eslint/prettier) and pre-commit
- [ ] E2E smoke test via docker-compose (API + frontend up)

## In Progress

- [ ] Backend: Database Migrations (Alembic)
- [ ] Backend: Document Management Skeleton
- [ ] Backend: Finalize Cerbos Integration

## Done

- [x] CI and basic backend test harness
- [x] Backend: configuration/settings module (env-driven)
- [x] Backend: Cerbos client integration (stub with health check)
- [x] Docker Compose: add Postgres, Redis, Cerbos services; wire env
- [x] Backend: auth skeleton (JWT, users model, login/refresh endpoints)
- [x] Backend: RBAC with Cerbos
- [x] Backend: Password Verification & Refresh Tokens