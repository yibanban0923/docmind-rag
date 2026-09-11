import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app

QUESTIONS_FILE = Path("eval/questions.jsonl")
OUTPUT_FILE = Path("eval/results/calibration_distances.json")


def load_questions() -> list[dict]:
    questions = []

    with QUESTIONS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))

    return questions


def main() -> None:
    settings = get_settings()
    app = create_app(settings=settings)

    questions = load_questions()
    rows: list[dict] = []

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with TestClient(app) as client:
        for index, case in enumerate(questions, start=1):
            case_id = case["case_id"]
            question = case["question"]

            print(
                f"[{index:02d}/{len(questions)}] "
                f"{case_id}: {question}"
            )

            response = client.post(
                "/retrieve",
                json={
                    "question": question,
                    "top_k": settings.TOP_K,
                },
            )

            if response.status_code != 200:
                print(
                    f"  -> retrieve failed: "
                    f"HTTP {response.status_code}"
                )

                rows.append(
                    {
                        "case_id": case_id,
                        "question": question,
                        "answerable": case["answerable"],
                        "expected_document": case.get(
                            "expected_document"
                        ),
                        "expected_locator": case.get(
                            "expected_locator"
                        ),
                        "best_distance": None,
                        "retrieve_failed": True,
                        "status_code": response.status_code,
                    }
                )

                continue

            body = response.json()
            items = body.get("items", [])

            if items:
                best_distance = min(
                    float(item["distance"])
                    for item in items
                    if item.get("distance") is not None
                )
            else:
                best_distance = None

            print(
                f"  -> best_distance = "
                f"{best_distance}"
            )

            rows.append(
                {
                    "case_id": case_id,
                    "question": question,
                    "answerable": case["answerable"],
                    "expected_document": case.get(
                        "expected_document"
                    ),
                    "expected_locator": case.get(
                        "expected_locator"
                    ),
                    "best_distance": best_distance,
                    "retrieve_failed": False,
                    "retrieved": items,
                }
            )

    output = {
        "top_k": settings.TOP_K,
        "embedding_model": settings.EMBEDDING_MODEL,
        "cases": rows,
    }

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("完成。")
    print(f"结果文件: {OUTPUT_FILE}")
    print(f"题目数量: {len(rows)}")


if __name__ == "__main__":
    main()