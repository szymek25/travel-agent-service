from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.db.dynamodb import create_tables
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting AI Travel Agent Service in '{settings.ENV}' environment")
    if settings.ENV == "development":
        create_tables()
    yield


app = FastAPI(
    title="AI Travel Agent Service",
    description="A FastAPI backend for an AI-powered travel agent with RAG and agent architecture.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "env": settings.ENV}
