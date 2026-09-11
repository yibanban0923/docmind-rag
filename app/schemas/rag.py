from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class RetrievedChunkResponse(BaseModel):
    rank: int
    distance: float
    text: str
    document_id: str
    filename: str
    file_type: str
    chunk_index: int
    page: int | None = None
    section: str | None = None


class RetrieveResponse(BaseModel):
    items: list[RetrievedChunkResponse]
    latency_ms: float
    request_id: str


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class SourceResponse(BaseModel):
    source_id: str
    document_id: str
    filename: str
    page: int | None = None
    section: str | None = None
    chunk_index: int
    excerpt: str


class LatencyResponse(BaseModel):
    retrieve: float
    llm: float
    total: float


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
    latency_ms: LatencyResponse
    request_id: str
