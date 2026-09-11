from fastapi import FastAPI

from app.container import build_container
from app.core.config import get_settings
from app.routers.documents import router as documents_router
from app.routers.health import router as health_router

settings = get_settings()
app = FastAPI(title=settings.APP_NAME, version="0.2.0", description="DocMind RAG backend API")
app.state.container = build_container(settings)
app.include_router(health_router)
app.include_router(documents_router)
