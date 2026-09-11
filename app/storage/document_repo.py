from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.core.exceptions import DuplicateDocumentError, StorageError
from app.storage.models import Document


@dataclass(slots=True)
class DocumentRecord:
    document_id: str
    filename: str
    file_type: str
    checksum: str
    chunk_count: int
    created_at: datetime


def _to_record(row: Document) -> DocumentRecord:
    return DocumentRecord(
        document_id=row.document_id,
        filename=row.filename,
        file_type=row.file_type,
        checksum=row.checksum,
        chunk_count=row.chunk_count,
        created_at=row.created_at,
    )


class DocumentRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def get(self, document_id: str) -> DocumentRecord | None:
        with self.session_factory() as db:
            row = db.get(Document, document_id)
            return _to_record(row) if row else None

    def get_by_checksum(self, checksum: str) -> DocumentRecord | None:
        with self.session_factory() as db:
            row = db.scalar(select(Document).where(Document.checksum == checksum))
            return _to_record(row) if row else None

    def list(self) -> list[DocumentRecord]:
        with self.session_factory() as db:
            rows = db.scalars(select(Document).order_by(Document.created_at.desc())).all()
            return [_to_record(row) for row in rows]

    def existing_ids(self, document_ids: set[str]) -> set[str]:
        if not document_ids:
            return set()
        with self.session_factory() as db:
            rows = db.scalars(select(Document.document_id).where(Document.document_id.in_(document_ids))).all()
            return set(rows)

    def create(
        self,
        *,
        document_id: str,
        filename: str,
        file_type: str,
        checksum: str,
        chunk_count: int,
    ) -> DocumentRecord:
        with self.session_factory() as db:
            row = Document(
                document_id=document_id,
                filename=filename,
                file_type=file_type,
                checksum=checksum,
                chunk_count=chunk_count,
            )
            db.add(row)
            try:
                db.commit()
                db.refresh(row)
                return _to_record(row)
            except IntegrityError as exc:
                db.rollback()
                raise DuplicateDocumentError() from exc
            except Exception as exc:
                db.rollback()
                raise StorageError("Failed to write document metadata") from exc

    def delete(self, document_id: str) -> None:
        with self.session_factory() as db:
            row = db.get(Document, document_id)
            if row is None:
                return
            db.delete(row)
            try:
                db.commit()
            except Exception as exc:
                db.rollback()
                raise StorageError("Failed to delete document metadata") from exc

    def ping(self) -> bool:
        with self.session_factory() as db:
            db.execute(select(Document.document_id).limit(1))
        return True
