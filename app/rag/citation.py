import re

from app.core.exceptions import ModelOutputInvalidError
from app.rag.types import ContextSource

SOURCE_PATTERN = re.compile(r"\[(S\d+)\]")


def validate_citations(answer: str, sources: list[ContextSource]) -> list[ContextSource]:
    allowed = {source.source_id: source for source in sources}
    cited_ids = SOURCE_PATTERN.findall(answer)
    unknown = sorted(set(cited_ids) - set(allowed))
    if unknown:
        raise ModelOutputInvalidError(details={"unknown_sources": unknown})
    if not cited_ids:
        raise ModelOutputInvalidError("Model answer did not include a valid source citation")

    ordered: list[ContextSource] = []
    seen: set[str] = set()
    for source_id in cited_ids:
        if source_id not in seen:
            ordered.append(allowed[source_id])
            seen.add(source_id)
    return ordered
