from app.rag.types import RetrievalResult

REFUSAL_TEXT = "无法从当前资料确认"


def has_sufficient_evidence(result: RetrievalResult, max_distance: float) -> bool:
    if not result.items:
        return False
    return result.items[0].distance <= max_distance
