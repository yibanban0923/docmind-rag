from dataclasses import dataclass

from app.clients.factory import build_embedding_client, build_llm_client
from app.core.config import Settings
from app.ingestion.service import IngestionService
from app.rag.pipeline import RAGPipeline
from app.rag.retriever import RetrievalService
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
    llm_client: object
    ingestion_service: IngestionService
    retrieval_service: RetrievalService
    rag_pipeline: RAGPipeline


def build_container(settings: Settings) -> AppContainer:
    settings.ensure_directories()
    database=Database(settings.sqlite_path)
    repo=DocumentRepository(database.session_factory)
    store=VectorStoreAdapter(settings.chroma_dir, settings.CHROMA_COLLECTION)
    embedding=build_embedding_client(settings)
    llm=build_llm_client(settings)
    ingestion=IngestionService(settings=settings, document_repo=repo, vector_store=store, embedding_client=embedding)
    retrieval=RetrievalService(document_repo=repo, vector_store=store, embedding_client=embedding, default_top_k=settings.TOP_K)
    rag=RAGPipeline(retriever=retrieval, llm_client=llm, max_distance=settings.MAX_DISTANCE, context_max_chars=settings.CONTEXT_MAX_CHARS)
    return AppContainer(settings,database,repo,store,embedding,llm,ingestion,retrieval,rag)
