from fastapi import FastAPI
from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title="AI Travel Agent Service",
    description="A FastAPI backend for an AI-powered travel agent with RAG and agent architecture.",
    version="0.1.0",
)

app.include_router(api_router)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "env": settings.ENV}
