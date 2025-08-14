from fastapi import FastAPI
from .core.config import get_settings
from .auth.router import router as auth_router

settings = get_settings()
app = FastAPI(title="RBAC-RAG for ERP", debug=settings.debug)
app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to RBAC-RAG for ERP"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "env": settings.env,
        "debug": settings.debug,
    }
