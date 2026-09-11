from dataclasses import dataclass

from app.clients.factory import build_embedding_client, build_llm_client
from app.core.config import Settings
from app.ingestion.service import IngestionService
from app.rag.pipeline import RAGPipeline
from app.rag.retriever import RetrievalService
from app.storage.database import Database
from app.storage.document_repo import DocumentRepository
from app.storage.document_service import DocumentService
from app.storage.vector_store import VectorStoreAdapter


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    database: Database
    document_repo: DocumentRepository
    vector_store: VectorStoreAdapter
    embedding_client: object
    llm_client: object
    ingestion_service: IngestionService
    retrieval_service: RetrievalService
    rag_pipeline: RAGPipeline
    document_service: DocumentService


def build_container(
    settings: Settings,
    *,
    embedding_client=None,
    llm_client=None,
) -> AppContainer:
    settings.ensure_directories()
    database = Database(settings.sqlite_path)
    document_repo = DocumentRepository(database.session_factory)
    vector_store = VectorStoreAdapter(settings.chroma_dir, settings.CHROMA_COLLECTION)
    embedding_client = embedding_client or build_embedding_client(settings)
    llm_client = llm_client or build_llm_client(settings)

    ingestion_service = IngestionService(
        settings=settings,
        document_repo=document_repo,
        vector_store=vector_store,
        embedding_client=embedding_client,
    )
    retrieval_service = RetrievalService(
        document_repo=document_repo,
        vector_store=vector_store,
        embedding_client=embedding_client,
        default_top_k=settings.TOP_K,
    )
    rag_pipeline = RAGPipeline(
        retriever=retrieval_service,
        llm_client=llm_client,
        max_distance=settings.MAX_DISTANCE,
        context_max_chars=settings.CONTEXT_MAX_CHARS,
    )
    document_service = DocumentService(document_repo, vector_store)
    return AppContainer(
        settings=settings,
        database=database,
        document_repo=document_repo,
        vector_store=vector_store,
        embedding_client=embedding_client,
        llm_client=llm_client,
        ingestion_service=ingestion_service,
        retrieval_service=retrieval_service,
        rag_pipeline=rag_pipeline,
        document_service=document_service,
    )
