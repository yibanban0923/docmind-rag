from pathlib import Path

import pytest

from app.core.exceptions import DuplicateDocumentError
from app.storage.database import Database
from app.storage.document_repo import DocumentRepository


def make_repo(tmp_path: Path):
    db = Database(tmp_path / "db.sqlite")
    return DocumentRepository(db.session_factory)


def test_create_and_get_document(tmp_path: Path):
    repo = make_repo(tmp_path)
    repo.create(document_id="d1", filename="a.md", file_type="md", checksum="a" * 64, chunk_count=1)
    assert repo.get("d1").filename == "a.md"


def test_checksum_is_unique(tmp_path: Path):
    repo = make_repo(tmp_path)
    checksum = "a" * 64
    repo.create(document_id="d1", filename="a.md", file_type="md", checksum=checksum, chunk_count=1)
    with pytest.raises(DuplicateDocumentError):
        repo.create(document_id="d2", filename="b.md", file_type="md", checksum=checksum, chunk_count=1)


def test_list_only_committed_documents(tmp_path: Path):
    repo = make_repo(tmp_path)
    repo.create(document_id="d1", filename="a.md", file_type="md", checksum="a" * 64, chunk_count=1)
    assert [item.document_id for item in repo.list()] == ["d1"]


def test_delete_is_idempotent_at_repository_level(tmp_path: Path):
    repo = make_repo(tmp_path)
    repo.create(document_id="d1", filename="a.md", file_type="md", checksum="a" * 64, chunk_count=1)
    repo.delete("d1")
    repo.delete("d1")
    assert repo.get("d1") is None
