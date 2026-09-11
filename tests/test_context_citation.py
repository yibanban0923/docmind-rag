import pytest

from app.core.exceptions import ModelOutputInvalidError
from app.rag.citation import validate_citations
from app.rag.context import build_context
from app.rag.types import RetrievedChunk


def chunk(rank=1, text="abc", distance=0.1):
    return RetrievedChunk(
        rank=rank,
        distance=distance,
        text=text,
        metadata={"document_id": "d1", "filename": "a.md", "file_type": "md", "chunk_index": rank - 1, "section": "A"},
    )


def test_context_assigns_source_labels():
    bundle = build_context([chunk(1), chunk(2)], 1000)
    assert [s.source_id for s in bundle.sources] == ["S1", "S2"]
    assert "[S1]" in bundle.context_text


def test_context_respects_budget():
    bundle = build_context([chunk(1, "x" * 500), chunk(2, "y" * 500)], 300)
    assert len(bundle.context_text) <= 300


def test_valid_citation_is_mapped():
    bundle = build_context([chunk()], 1000)
    cited = validate_citations("answer [S1]", bundle.sources)
    assert cited[0].source_id == "S1"


def test_unknown_citation_is_rejected():
    bundle = build_context([chunk()], 1000)
    with pytest.raises(ModelOutputInvalidError):
        validate_citations("answer [S9]", bundle.sources)


def test_missing_citation_is_rejected():
    bundle = build_context([chunk()], 1000)
    with pytest.raises(ModelOutputInvalidError):
        validate_citations("answer without citation", bundle.sources)
