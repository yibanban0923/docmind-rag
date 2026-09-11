from fastapi import FastAPI

from app.container import build_container
from app.core.config import Settings, get_settings
from app.core.error_handlers import register_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.routers.documents import router as documents_router
from app.routers.health import router as health_router
from app.routers.rag import router as rag_router


def create_app(
    *,
    settings: Settings | None = None,
    embedding_client=None,
    llm_client=None,
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging()
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="Document retrieval-augmented generation knowledge base API",
    )
    app.state.container = build_container(
        settings,
        embedding_client=embedding_client,
        llm_client=llm_client,
    )
    app.add_middleware(RequestContextMiddleware)
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(documents_router)
    app.include_router(rag_router)
    return app


app = create_app()
