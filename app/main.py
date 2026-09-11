from fastapi import FastAPI

from app.container import build_container
from app.core.config import get_settings
from app.core.middleware import RequestContextMiddleware
from app.routers.documents import router as documents_router
from app.routers.health import router as health_router
from app.routers.rag import router as rag_router

settings=get_settings()
app=FastAPI(title=settings.APP_NAME, version="0.3.0")
app.state.container=build_container(settings)
app.add_middleware(RequestContextMiddleware)
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(rag_router)
