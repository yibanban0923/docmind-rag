from app.rag.types import ContextBundle, ContextSource, RetrievedChunk


def _locator(chunk: RetrievedChunk) -> str:
    page = chunk.metadata.get("page")
    section = chunk.metadata.get("section")
    if page is not None:
        return f"page={page}"
    if section:
        return f"section={section}"
    return "locator=unknown"


def build_context(items: list[RetrievedChunk], max_chars: int) -> ContextBundle:
    blocks: list[str] = []
    sources: list[ContextSource] = []
    used = 0
    for index, chunk in enumerate(items, start=1):
        source_id = f"S{index}"
        header = (
            f"[{source_id}] filename={chunk.metadata.get('filename')} "
            f"{_locator(chunk)} chunk_index={chunk.metadata.get('chunk_index')}"
        )
        remaining = max_chars - used - len(header) - 2
        if remaining <= 0:
            break
        excerpt = chunk.text[:remaining]
        if not excerpt:
            break
        block = f"{header}\n{excerpt}"
        blocks.append(block)
        sources.append(ContextSource(source_id=source_id, chunk=chunk, excerpt=excerpt[:500]))
        used += len(block) + 2
    return ContextBundle(context_text="\n\n".join(blocks), sources=sources)
