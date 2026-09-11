import time

from app.clients.base import EmbeddingClient
from app.rag.types import RetrievalResult, RetrievedChunk
from app.storage.document_repo import DocumentRepository
from app.storage.vector_store import VectorStoreAdapter


class RetrievalService:
    def __init__(
        self,
        *,
        document_repo: DocumentRepository,
        vector_store: VectorStoreAdapter,
        embedding_client: EmbeddingClient,
        default_top_k: int,
    ):
        self.document_repo = document_repo
        self.vector_store = vector_store
        self.embedding_client = embedding_client
        self.default_top_k = default_top_k

    def retrieve(self, question: str, *, top_k: int | None = None) -> RetrievalResult:
        started = time.perf_counter()
        k = top_k or self.default_top_k
        query_embedding = self.embedding_client.embed_query(question)
        raw_hits = self.vector_store.query(query_embedding, n_results=max(k * 3, k))

        document_ids = {
            str(hit.metadata.get("document_id"))
            for hit in raw_hits
            if hit.metadata.get("document_id")
        }
        valid_ids = self.document_repo.existing_ids(document_ids)

        items: list[RetrievedChunk] = []
        for hit in raw_hits:
            document_id = str(hit.metadata.get("document_id", ""))
            if document_id not in valid_ids:
                continue
            items.append(
                RetrievedChunk(
                    rank=len(items) + 1,
                    distance=hit.distance,
                    text=hit.text,
                    metadata=hit.metadata,
                )
            )
            if len(items) >= k:
                break

        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return RetrievalResult(items=items, latency_ms=latency_ms)
