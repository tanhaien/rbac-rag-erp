from fastapi import FastAPI

app = FastAPI(title="RBAC-RAG for ERP")

@app.get("/")
def read_root():
    return {"message": "Welcome to RBAC-RAG for ERP"}
