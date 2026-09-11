import json
from pathlib import Path

INPUT_FILE = Path("eval/results/calibration_distances.json")


def load_cases() -> list[dict]:
    with INPUT_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return [
        case
        for case in data["cases"]
        if case.get("best_distance") is not None
    ]


def evaluate_threshold(cases: list[dict], threshold: float) -> dict:
    tp = 0
    tn = 0
    fp = 0
    fn = 0

    for case in cases:
        answerable = bool(case["answerable"])
        distance = float(case["best_distance"])

        predicted_answerable = distance <= threshold

        if answerable and predicted_answerable:
            tp += 1
        elif not answerable and not predicted_answerable:
            tn += 1
        elif not answerable and predicted_answerable:
            fp += 1
        elif answerable and not predicted_answerable:
            fn += 1

    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total else 0.0

    answerable_total = tp + fn
    no_answer_total = tn + fp

    answerable_recall = (
        tp / answerable_total
        if answerable_total
        else 0.0
    )

    no_answer_accuracy = (
        tn / no_answer_total
        if no_answer_total
        else 0.0
    )

    return {
        "threshold": threshold,
        "accuracy": accuracy,
        "answerable_recall": answerable_recall,
        "no_answer_accuracy": no_answer_accuracy,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def main() -> None:
    cases = load_cases()

    answerable = [
        float(c["best_distance"])
        for c in cases
        if c["answerable"]
    ]

    unanswerable = [
        float(c["best_distance"])
        for c in cases
        if not c["answerable"]
    ]

    print("=== Distance 分布 ===")

    if answerable:
        print(
            "可回答:",
            f"min={min(answerable):.4f}",
            f"max={max(answerable):.4f}",
            f"avg={sum(answerable)/len(answerable):.4f}",
        )

    if unanswerable:
        print(
            "无答案:",
            f"min={min(unanswerable):.4f}",
            f"max={max(unanswerable):.4f}",
            f"avg={sum(unanswerable)/len(unanswerable):.4f}",
        )

    distances = sorted(
        {
            round(float(c["best_distance"]), 6)
            for c in cases
        }
    )

    candidates = []

    for i in range(len(distances) - 1):
        candidates.append(
            (distances[i] + distances[i + 1]) / 2
        )

    candidates.extend(distances)

    results = [
        evaluate_threshold(cases, threshold)
        for threshold in candidates
    ]

    results.sort(
        key=lambda r: (
            r["accuracy"],
            r["no_answer_accuracy"],
            r["answerable_recall"],
        ),
        reverse=True,
    )

    print()
    print("=== 最佳候选 ===")

    for result in results[:10]:
        print(
            f"threshold={result['threshold']:.4f} "
            f"accuracy={result['accuracy']:.3f} "
            f"answerable_recall={result['answerable_recall']:.3f} "
            f"no_answer_accuracy={result['no_answer_accuracy']:.3f} "
            f"FP={result['fp']} "
            f"FN={result['fn']}"
        )

    best = results[0]

    print()
    print(
        "Suggested threshold:",
        round(best["threshold"], 4),
    )

    print()
    print("=== 最佳阈值错误案例 ===")

    threshold = best["threshold"]

    for case in cases:
        predicted_answerable = (
            float(case["best_distance"]) <= threshold
        )

        if predicted_answerable != bool(case["answerable"]):
            print(
                case["case_id"],
                "answerable=",
                case["answerable"],
                "distance=",
                round(float(case["best_distance"]), 4),
                "question=",
                case["question"],
            )


if __name__ == "__main__":
    main()