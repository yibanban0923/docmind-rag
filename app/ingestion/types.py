from dataclasses import dataclass


@dataclass(slots=True)
class LoadedUnit:
    text: str
    page: int | None = None
    section: str | None = None


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    document_id: str
    filename: str
    file_type: str
    chunk_index: int
    text: str
    page: int | None = None
    section: str | None = None

    def chroma_metadata(self) -> dict[str, str | int]:
        metadata: dict[str, str | int] = {
            "document_id": self.document_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "chunk_index": self.chunk_index,
        }
        if self.page is not None:
            metadata["page"] = self.page
        if self.section is not None:
            metadata["section"] = self.section
        return metadata
