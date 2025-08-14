from contextlib import asynccontextmanager
from fastapi import FastAPI
from .core.config import get_settings
from .auth.router import router as auth_router
from .cerbos.client import cerbos_client
from .core.db import create_all_if_configured

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_all_if_configured()
    yield
    # Shutdown


app = FastAPI(title="RBAC-RAG for ERP", debug=settings.debug, lifespan=lifespan)
app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to RBAC-RAG for ERP"}


@app.get("/health")
def health():
    cerbos = cerbos_client.health()
    return {
        "status": "ok",
        "env": settings.env,
        "debug": settings.debug,
        "cerbos": {"ok": cerbos.ok, "host": cerbos.host, "error": cerbos.error},
    }
