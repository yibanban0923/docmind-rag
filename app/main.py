from fastapi import FastAPI

from app.core.config import get_settings
from app.routers.health import router as health_router

settings = get_settings()
settings.ensure_directories()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="DocMind RAG backend API",
)
app.include_router(health_router)
