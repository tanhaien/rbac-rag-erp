# TODO

Feature-by-feature task tracker for RBAC-RAG (Gemini-led).

## Backlog
- [x] CI and basic backend test harness
- [x] Backend: configuration/settings module (env-driven)
- [ ] Backend: auth skeleton (JWT, users model, login/refresh endpoints)
  - [x] Minimal JWT and /auth/login, /auth/me endpoints (no DB yet)
  - [ ] Users/roles models wired to DB and refresh endpoint
- [ ] Backend: Cerbos client integration (stub with health check)
- [ ] Backend: document ingestion API stub and validation
- [ ] Backend: RAG pipeline skeleton (interfaces only)
- [ ] Docker Compose: add Postgres, Redis, Cerbos services; wire env
- [ ] Frontend: bootstrap app shell and health page
- [ ] Tooling: lint/format (ruff/black; eslint/prettier) and pre-commit
- [ ] E2E smoke test via docker-compose (API + frontend up)

## In Progress
- None

## Done
- CI + basic tests scaffolded (2025-08-14)
