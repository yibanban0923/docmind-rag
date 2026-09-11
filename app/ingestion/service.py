import time
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.clients.base import EmbeddingClient
from app.core.config import Settings
from app.core.exceptions import (
    DuplicateDocumentError,
    StorageError,
    UnsupportedDocumentError,
)
from app.core.logging import log_event
from app.ingestion.cleaner import clean_units
from app.ingestion.loader import load_document
from app.ingestion.splitter import split_units
from app.ingestion.upload import save_upload_to_temp
from app.storage.document_repo import DocumentRecord, DocumentRepository
from app.storage.vector_store import VectorStoreAdapter


class IngestionService:
    def __init__(
        self,
        *,
        settings: Settings,
        document_repo: DocumentRepository,
        vector_store: VectorStoreAdapter,
        embedding_client: EmbeddingClient,
    ):
        self.settings = settings
        self.document_repo = document_repo
        self.vector_store = vector_store
        self.embedding_client = embedding_client

    def _embed_batches(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        size = self.settings.EMBED_BATCH_SIZE
        for start in range(0, len(texts), size):
            embeddings.extend(self.embedding_client.embed_documents(texts[start : start + size]))
        return embeddings

    def index_path(
        self,
        *,
        path: Path,
        filename: str,
        file_type: str,
        checksum: str,
        request_id: str | None = None,
    ) -> DocumentRecord:
        if self.document_repo.get_by_checksum(checksum):
            raise DuplicateDocumentError()

        document_id = str(uuid.uuid4())
        parse_started = time.perf_counter()
        units = clean_units(load_document(path, file_type))
        if not units:
            raise UnsupportedDocumentError()
        chunks = split_units(
            document_id=document_id,
            filename=filename,
            file_type=file_type,
            units=units,
            chunk_size=self.settings.CHUNK_SIZE,
            overlap=self.settings.CHUNK_OVERLAP,
        )
        if not chunks:
            raise UnsupportedDocumentError()
        parse_ms = round((time.perf_counter() - parse_started) * 1000, 2)

        embed_started = time.perf_counter()
        embeddings = self._embed_batches([chunk.text for chunk in chunks])
        embed_ms = round((time.perf_counter() - embed_started) * 1000, 2)

        index_started = time.perf_counter()
        self.vector_store.add(chunks, embeddings)
        try:
            vector_count = self.vector_store.count_by_document(document_id)
            if vector_count != len(chunks):
                raise StorageError("Indexed vector count does not match chunk_count")
            record = self.document_repo.create(
                document_id=document_id,
                filename=filename,
                file_type=file_type,
                checksum=checksum,
                chunk_count=len(chunks),
            )
        except Exception:
            try:
                self.vector_store.delete_by_document(document_id)
            except Exception as compensation_error:
                log_event(
                    "ingestion_compensation_failed",
                    request_id=request_id,
                    document_id=document_id,
                    exception_type=type(compensation_error).__name__,
                )
            raise
        index_ms = round((time.perf_counter() - index_started) * 1000, 2)

        log_event(
            "ingestion_complete",
            request_id=request_id,
            document_id=document_id,
            chunk_count=len(chunks),
            parse_ms=parse_ms,
            embed_ms=embed_ms,
            index_ms=index_ms,
        )
        return record

    async def ingest_upload(self, upload: UploadFile, *, request_id: str | None = None) -> DocumentRecord:
        saved = await save_upload_to_temp(
            upload,
            temp_dir=self.settings.temp_dir,
            max_bytes=self.settings.max_upload_bytes,
        )
        try:
            return self.index_path(
                path=saved.path,
                filename=saved.filename,
                file_type=saved.file_type,
                checksum=saved.checksum,
                request_id=request_id,
            )
        finally:
            saved.path.unlink(missing_ok=True)
