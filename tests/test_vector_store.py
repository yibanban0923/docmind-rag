from pathlib import Path

from app.clients.fake import FakeEmbeddingClient
from app.ingestion.types import Chunk
from app.storage.vector_store import VectorStoreAdapter


def make_chunk(document_id: str, text: str, index: int = 0):
    return Chunk(
        chunk_id=f"{document_id}-{index}",
        document_id=document_id,
        filename="a.md",
        file_type="md",
        chunk_index=index,
        text=text,
        section="A",
    )


def test_add_query_delete(tmp_path: Path):
    store = VectorStoreAdapter(tmp_path / "chroma", "test")
    embed = FakeEmbeddingClient()
    chunks = [make_chunk("d1", "python fastapi"), make_chunk("d2", "mysql database")]
    store.add(chunks, embed.embed_documents([c.text for c in chunks]))
    assert store.count_by_document("d1") == 1
    hits = store.query(embed.embed_query("python"), 2)
    assert len(hits) == 2
    store.delete_by_document("d1")
    assert store.count_by_document("d1") == 0


def test_metadata_contains_locator(tmp_path: Path):
    store = VectorStoreAdapter(tmp_path / "chroma", "test")
    embed = FakeEmbeddingClient()
    chunk = make_chunk("d1", "hello")
    store.add([chunk], embed.embed_documents([chunk.text]))
    hit = store.query(embed.embed_query("hello"), 1)[0]
    assert hit.metadata["section"] == "A"
