from fastapi import APIRouter, Depends, Request

from app.container import AppContainer
from app.deps import get_container
from app.schemas.rag import (
    AskRequest,
    AskResponse,
    RetrievedChunkResponse,
    RetrieveRequest,
    RetrieveResponse,
)

router = APIRouter(tags=["RAG"])


def _chunk_to_response(chunk) -> RetrievedChunkResponse:
    metadata = chunk.metadata
    return RetrievedChunkResponse(
        rank=chunk.rank,
        distance=chunk.distance,
        text=chunk.text,
        document_id=str(metadata.get("document_id")),
        filename=str(metadata.get("filename")),
        file_type=str(metadata.get("file_type")),
        chunk_index=int(metadata.get("chunk_index", 0)),
        page=int(metadata["page"]) if metadata.get("page") is not None else None,
        section=str(metadata["section"]) if metadata.get("section") is not None else None,
    )


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(
    payload: RetrieveRequest,
    request: Request,
    container: AppContainer = Depends(get_container),
):
    result = container.retrieval_service.retrieve(payload.question, top_k=payload.top_k)
    return RetrieveResponse(
        items=[_chunk_to_response(item) for item in result.items],
        latency_ms=result.latency_ms,
        request_id=request.state.request_id,
    )


@router.post("/ask", response_model=AskResponse)
def ask(
    payload: AskRequest,
    request: Request,
    container: AppContainer = Depends(get_container),  # noqa: B008
):
    result = container.rag_pipeline.ask(payload.question, request_id=request.state.request_id)
    sources = []
    for source in result["sources"]:
        metadata = source.chunk.metadata
        sources.append(
            {
                "source_id": source.source_id,
                "document_id": str(metadata.get("document_id")),
                "filename": str(metadata.get("filename")),
                "page": int(metadata["page"]) if metadata.get("page") is not None else None,
                "section": str(metadata["section"]) if metadata.get("section") is not None else None,
                "chunk_index": int(metadata.get("chunk_index", 0)),
                "excerpt": source.excerpt,
            }
        )
    return {
        "answer": result["answer"],
        "sources": sources,
        "latency_ms": {
            "retrieve": result["retrieve_ms"],
            "llm": result["llm_ms"],
            "total": result["total_ms"],
        },
        "request_id": request.state.request_id,
    }
