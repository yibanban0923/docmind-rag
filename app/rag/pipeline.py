import time

from app.clients.base import LLMClient
from app.core.logging import log_event
from app.rag.citation import validate_citations
from app.rag.context import build_context
from app.rag.gate import REFUSAL_TEXT, has_sufficient_evidence
from app.rag.prompt import SYSTEM_PROMPT, build_user_prompt
from app.rag.retriever import RetrievalService


class RAGPipeline:
    def __init__(
        self,
        *,
        retriever: RetrievalService,
        llm_client: LLMClient,
        max_distance: float,
        context_max_chars: int,
    ):
        self.retriever = retriever
        self.llm_client = llm_client
        self.max_distance = max_distance
        self.context_max_chars = context_max_chars

    def ask(self, question: str, *, request_id: str | None = None) -> dict:
        total_started = time.perf_counter()
        retrieval = self.retriever.retrieve(question)
        best_distance = retrieval.items[0].distance if retrieval.items else None

        if not has_sufficient_evidence(retrieval, self.max_distance):
            total_ms = round((time.perf_counter() - total_started) * 1000, 2)
            log_event(
                "rag_refusal",
                request_id=request_id,
                top_k=len(retrieval.items),
                best_distance=best_distance,
                retrieve_ms=retrieval.latency_ms,
                llm_ms=0.0,
                total_ms=total_ms,
            )
            return {
                "answer": REFUSAL_TEXT,
                "sources": [],
                "retrieve_ms": retrieval.latency_ms,
                "llm_ms": 0.0,
                "total_ms": total_ms,
            }

        bundle = build_context(retrieval.items, self.context_max_chars)
        llm_started = time.perf_counter()
        answer = self.llm_client.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(question, bundle.context_text),
        )
        llm_ms = round((time.perf_counter() - llm_started) * 1000, 2)
        cited_sources = validate_citations(answer, bundle.sources)
        total_ms = round((time.perf_counter() - total_started) * 1000, 2)
        log_event(
            "rag_answer",
            request_id=request_id,
            top_k=len(retrieval.items),
            best_distance=best_distance,
            retrieve_ms=retrieval.latency_ms,
            llm_ms=llm_ms,
            total_ms=total_ms,
        )
        return {
            "answer": answer,
            "sources": cited_sources,
            "retrieve_ms": retrieval.latency_ms,
            "llm_ms": llm_ms,
            "total_ms": total_ms,
        }
