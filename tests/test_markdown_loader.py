from pathlib import Path

import pytest

from app.core.exceptions import UnsupportedDocumentError
from app.ingestion.loader import load_markdown


def test_markdown_preserves_heading_path(tmp_path: Path):
    path = tmp_path / "sample.md"
    path.write_text("# A\nintro\n## B\nbody", encoding="utf-8")
    units = load_markdown(path)
    assert units[0].section == "A"
    assert units[1].section == "A / B"


def test_markdown_requires_utf8(tmp_path: Path):
    path = tmp_path / "bad.md"
    path.write_bytes(b"\xff\xfe\x00")
    with pytest.raises(UnsupportedDocumentError):
        load_markdown(path)


def test_markdown_root_section(tmp_path: Path):
    path = tmp_path / "root.md"
    path.write_text("plain text", encoding="utf-8")
    units = load_markdown(path)
    assert units[0].section == "ROOT"
