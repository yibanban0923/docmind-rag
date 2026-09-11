from app.ingestion.cleaner import clean_text
from app.ingestion.splitter import split_text, split_units
from app.ingestion.types import LoadedUnit


def test_cleaner_normalizes_whitespace():
    assert clean_text("a   b\r\n\r\n\r\nc") == "a b\n\nc"


def test_split_short_text_is_single_chunk():
    assert split_text("hello", 100, 10) == ["hello"]


def test_split_long_text_creates_multiple_chunks():
    chunks = split_text("word " * 100, 100, 20)
    assert len(chunks) > 1
    assert all(chunks)


def test_pdf_unit_keeps_page_metadata():
    chunks = split_units(
        document_id="d1",
        filename="a.pdf",
        file_type="pdf",
        units=[LoadedUnit(text="abc " * 80, page=2)],
        chunk_size=100,
        overlap=20,
    )
    assert {chunk.page for chunk in chunks} == {2}
    assert all(chunk.section is None for chunk in chunks)


def test_markdown_unit_keeps_section_metadata():
    chunks = split_units(
        document_id="d1",
        filename="a.md",
        file_type="md",
        units=[LoadedUnit(text="abc " * 80, section="A / B")],
        chunk_size=100,
        overlap=20,
    )
    assert {chunk.section for chunk in chunks} == {"A / B"}
