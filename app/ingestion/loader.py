import re
from pathlib import Path

from pypdf import PdfReader

from app.core.exceptions import UnsupportedDocumentError
from app.ingestion.types import LoadedUnit


def load_pdf(path: Path) -> list[LoadedUnit]:
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            raise UnsupportedDocumentError("Encrypted PDF is not supported")
        units: list[LoadedUnit] = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            units.append(LoadedUnit(text=text, page=page_number))
        return units
    except UnsupportedDocumentError:
        raise
    except Exception as exc:
        raise UnsupportedDocumentError("PDF cannot be parsed") from exc


def _heading_path(stack: list[str | None]) -> str:
    return " / ".join(item for item in stack if item)


def load_markdown(path: Path) -> list[LoadedUnit]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise UnsupportedDocumentError("Markdown must be UTF-8") from exc

    heading_re = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
    stack: list[str | None] = [None] * 6
    current_section = "ROOT"
    buffer: list[str] = []
    units: list[LoadedUnit] = []

    def flush() -> None:
        nonlocal buffer
        body = "\n".join(buffer).strip()
        if body:
            units.append(LoadedUnit(text=body, section=current_section))
        buffer = []

    for line in text.splitlines():
        match = heading_re.match(line)
        if match:
            flush()
            level = len(match.group(1))
            title = match.group(2).strip()
            stack[level - 1] = title
            for index in range(level, 6):
                stack[index] = None
            current_section = _heading_path(stack) or "ROOT"
        else:
            buffer.append(line)
    flush()
    return units


def load_document(path: Path, file_type: str) -> list[LoadedUnit]:
    if file_type == "pdf":
        return load_pdf(path)
    if file_type == "md":
        return load_markdown(path)
    raise UnsupportedDocumentError("Only PDF and Markdown are supported")
