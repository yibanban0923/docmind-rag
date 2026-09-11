from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    checksum: str
    chunk_count: int
    created_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
