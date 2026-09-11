from app.core.exceptions import DocumentNotFoundError, StorageError
from app.storage.document_repo import DocumentRepository
from app.storage.vector_store import VectorStoreAdapter


class DocumentService:
    def __init__(self, document_repo: DocumentRepository, vector_store: VectorStoreAdapter):
        self.document_repo = document_repo
        self.vector_store = vector_store

    def delete(self, document_id: str) -> None:
        record = self.document_repo.get(document_id)
        if record is None:
            raise DocumentNotFoundError()

        self.vector_store.delete_by_document(document_id)
        if self.vector_store.count_by_document(document_id) != 0:
            raise StorageError("Vector deletion could not be verified")

        self.document_repo.delete(document_id)
