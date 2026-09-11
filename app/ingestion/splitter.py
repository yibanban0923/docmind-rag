import uuid

from app.ingestion.types import Chunk, LoadedUnit


def split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    pieces: list[str] = []
    start = 0
    length = len(text)
    while start < length:
        hard_end = min(start + chunk_size, length)
        end = hard_end
        if hard_end < length:
            window = text[start:hard_end]
            candidates = [window.rfind("\n\n"), window.rfind("\n"), window.rfind(" ")]
            best = max(candidates)
            if best >= int(chunk_size * 0.6):
                end = start + best
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= length:
            break
        next_start = max(0, end - overlap)
        if next_start <= start:
            next_start = end
        start = next_start
    return pieces


def split_units(
    *,
    document_id: str,
    filename: str,
    file_type: str,
    units: list[LoadedUnit],
    chunk_size: int,
    overlap: int,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    chunk_index = 0
    for unit in units:
        for text in split_text(unit.text, chunk_size, overlap):
            chunks.append(
                Chunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document_id,
                    filename=filename,
                    file_type=file_type,
                    chunk_index=chunk_index,
                    text=text,
                    page=unit.page,
                    section=unit.section,
                )
            )
            chunk_index += 1
    return chunks
