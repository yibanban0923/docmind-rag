from dataclasses import dataclass

from app.clients.embeddings import OpenAICompatibleEmbeddingClient
from app.clients.fake import FakeEmbeddingClient
from app.core.config import Settings
from app.ingestion.service import IngestionService
from app.storage.database import Database
from app.storage.document_repo import DocumentRepository
from app.storage.vector_store import VectorStoreAdapter


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    database: Database
    document_repo: DocumentRepository
    vector_store: VectorStoreAdapter
    embedding_client: object
    ingestion_service: IngestionService


def build_container(settings: Settings) -> AppContainer:
    settings.ensure_directories()
    database = Database(settings.sqlite_path)
    repo = DocumentRepository(database.session_factory)
    store = VectorStoreAdapter(settings.chroma_dir, settings.CHROMA_COLLECTION)
    if settings.MODEL_MODE == "fake":
        embedding = FakeEmbeddingClient()
    else:
        missing = settings.missing_real_model_config()
        if missing:
            raise RuntimeError(f"Missing model config: {missing}")
        embedding = OpenAICompatibleEmbeddingClient(
            endpoint=settings.EMBEDDING_ENDPOINT or "",
            api_key=settings.EMBEDDING_API_KEY or "",
            model=settings.EMBEDDING_MODEL or "",
            timeout_seconds=settings.MODEL_TIMEOUT_SECONDS,
            max_retries=settings.MODEL_MAX_RETRIES,
        )
    ingestion = IngestionService(settings=settings, document_repo=repo, vector_store=store, embedding_client=embedding)
    return AppContainer(settings, database, repo, store, embedding, ingestion)
