from __future__ import annotations

from statistics import mean
from typing import Any


def locator_matches(item: dict, expected_locator) -> bool:
    if expected_locator is None:
        return True

    # 兼容 {"page": 3} / {"section": "..."}
    if isinstance(expected_locator, dict):
        for key, value in expected_locator.items():
            if item.get(key) != value:
                return False
        return True

    # 兼容 "page:3" / "section:xxx"
    if isinstance(expected_locator, str):
        value = expected_locator.strip()

        if value.startswith("page:"):
            try:
                expected_page = int(value.split(":", 1)[1].strip())
            except ValueError:
                return False

            return item.get("page") == expected_page

        if value.startswith("section:"):
            expected_section = value.split(":", 1)[1].strip()
            return item.get("section") == expected_section

    return False


def recall_hit(items: list[dict[str, Any]], expected_document: str, expected_locator: dict[str, Any]) -> bool:
    return any(
        item.get("filename") == expected_document and locator_matches(item, expected_locator)
        for item in items
    )


def percentile95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(0.95 * (len(ordered) - 1))))
    return ordered[index]


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    answerable = [row for row in rows if row["answerable"]]
    no_answer = [row for row in rows if not row["answerable"]]
    recall = sum(bool(row.get("recall_hit")) for row in answerable) / len(answerable) if answerable else 0.0
    no_answer_accuracy = sum(bool(row.get("refused")) for row in no_answer) / len(no_answer) if no_answer else 0.0
    false_refusal_rate = sum(bool(row.get("refused")) for row in answerable) / len(answerable) if answerable else 0.0
    retrieve = [float(row["retrieve_ms"]) for row in rows]
    llm = [float(row["llm_ms"]) for row in rows]
    total = [float(row["total_ms"]) for row in rows]
    return {
        "recall_at_k": recall,
        "no_answer_accuracy": no_answer_accuracy,
        "false_refusal_rate": false_refusal_rate,
        "latency_ms": {
            "retrieve_avg": mean(retrieve) if retrieve else 0.0,
            "retrieve_p95": percentile95(retrieve),
            "llm_avg": mean(llm) if llm else 0.0,
            "llm_p95": percentile95(llm),
            "total_avg": mean(total) if total else 0.0,
            "total_p95": percentile95(total),
        },
    }
