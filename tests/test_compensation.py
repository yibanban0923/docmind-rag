
from app.core.exceptions import StorageError


def test_metadata_failure_triggers_vector_compensation(app, client, monkeypatch):
    repo = app.state.container.document_repo
    vector_store = app.state.container.vector_store

    def fail_create(**kwargs):
        raise StorageError("forced metadata failure")

    monkeypatch.setattr(repo, "create", fail_create)
    response = client.post(
        "/documents",
        files={"file": ("note.md", b"# A\ncontent for compensation", "text/markdown")},
    )
    assert response.status_code == 500
    assert vector_store.collection.count() == 0
