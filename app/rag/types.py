from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RetrievedChunk:
    rank: int
    distance: float
    text: str
    metadata: dict[str, Any]


@dataclass(slots=True)
class RetrievalResult:
    items: list[RetrievedChunk]
    latency_ms: float


@dataclass(slots=True)
class ContextSource:
    source_id: str
    chunk: RetrievedChunk
    excerpt: str


@dataclass(slots=True)
class ContextBundle:
    context_text: str
    sources: list[ContextSource]
