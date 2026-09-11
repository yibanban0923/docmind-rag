from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.rag.gate import REFUSAL_TEXT
from eval.metrics import recall_hit, summarize

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "data" / "sample"
QUESTION_FILE = ROOT / "eval" / "questions.jsonl"
RESULT_DIR = ROOT / "eval" / "results"
WORK_DIR = ROOT / "eval" / "work"

CONFIGS = {
    "baseline_a": {"chunk_size": 700, "overlap": 100, "top_k": 3},
    "chunk_b": {"chunk_size": 1000, "overlap": 150, "top_k": 3},
    "topk_c": {"chunk_size": 700, "overlap": 100, "top_k": 5},
}


def load_questions() -> list[dict]:
    rows = [json.loads(line) for line in QUESTION_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    answerable = sum(bool(row["answerable"]) for row in rows)
    if len(rows) != 30 or answerable != 24:
        raise RuntimeError(f"questions.jsonl must contain exactly 30 cases: 24 answerable + 6 no-answer; got {len(rows)} / {answerable}")
    return rows


def upload_samples(client: TestClient) -> None:
    files = sorted([*SAMPLE_DIR.glob("*.pdf"), *SAMPLE_DIR.glob("*.md")])
    if not files:
        raise RuntimeError("No public sample PDF/Markdown files found in data/sample")
    for path in files:
        content_type = "application/pdf" if path.suffix.lower() == ".pdf" else "text/markdown"
        with path.open("rb") as handle:
            response = client.post("/documents", files={"file": (path.name, handle, content_type)})
        if response.status_code != 201:
            raise RuntimeError(f"Failed to index {path.name}: {response.status_code} {response.text}")


def run_one(config_id: str) -> dict:
    config = CONFIGS[config_id]
    data_dir = WORK_DIR / config_id
    if data_dir.exists():
        shutil.rmtree(data_dir)

    base = Settings()
    settings = Settings(
        _env_file=None,
        APP_NAME=base.APP_NAME,
        APP_ENV="evaluation",
        MODEL_MODE="real",
        LLM_API_KEY=base.LLM_API_KEY,
        LLM_ENDPOINT=base.LLM_ENDPOINT,
        LLM_MODEL=base.LLM_MODEL,
        EMBEDDING_API_KEY=base.EMBEDDING_API_KEY,
        EMBEDDING_ENDPOINT=base.EMBEDDING_ENDPOINT,
        EMBEDDING_MODEL=base.EMBEDDING_MODEL,
        MODEL_TIMEOUT_SECONDS=base.MODEL_TIMEOUT_SECONDS,
        MODEL_MAX_RETRIES=base.MODEL_MAX_RETRIES,
        DATA_DIR=data_dir,
        CHUNK_SIZE=config["chunk_size"],
        CHUNK_OVERLAP=config["overlap"],
        TOP_K=config["top_k"],
        MAX_DISTANCE=base.MAX_DISTANCE,
        CONTEXT_MAX_CHARS=base.CONTEXT_MAX_CHARS,
        MAX_UPLOAD_MB=base.MAX_UPLOAD_MB,
        EMBED_BATCH_SIZE=base.EMBED_BATCH_SIZE,
        CHROMA_COLLECTION=base.CHROMA_COLLECTION,
    )
    app = create_app(settings=settings)
    questions = load_questions()
    rows: list[dict] = []

    with TestClient(app) as client:
        upload_samples(client)
        for case in questions:
            retrieve = client.post("/retrieve", json={"question": case["question"], "top_k": config["top_k"]})
            retrieve.raise_for_status()
            retrieve_body = retrieve.json()
            ask = client.post("/ask", json={"question": case["question"]})
            ask_failed = ask.status_code != 200
            if ask_failed:
                try:
                    error_body = ask.json()
                except Exception:
                    error_body = {"message":ask.text}
                
                ask_body = {
                    "answer":"",
                    "sources":[],
                    "latency_ms":{
                        "retrieve":0,
                        "llm":0,
                        "total":0,
                    },
                    "error":{
                        "status_code":ask.status_code,
                        "body":error_body,
                    },
                }
            else:
                ask_body = ask.json()

            row = {
                    "case_id": case["case_id"],
                    "question": case["question"],
                    "answerable": case["answerable"],
                    "expected_document": case.get(
                        "expected_document"
                    ),
                    "expected_locator": case.get(
                        "expected_locator"
                    ),
                    "recall_hit": None,
                    "refused": (
                        False
                        if ask_failed
                        else ask_body["answer"] == REFUSAL_TEXT
                    ),
                    "retrieve_ms": (
                        ask_body["latency_ms"]["retrieve"]
                        if not ask_failed
                        else 0
                    ),
                    "llm_ms": (
                        ask_body["latency_ms"]["llm"]
                        if not ask_failed
                         else 0
                    ),
                    "total_ms": (
                        ask_body["latency_ms"]["total"]
                        if not ask_failed
                        else 0
                    ),
                "retrieved": retrieve_body["items"],
                "answer": ask_body["answer"],
                "ask_failed": ask_failed,
                "ask_status_code": ask.status_code,
            }
            if case["answerable"]:
                row["recall_hit"] = recall_hit(
                    retrieve_body["items"],
                    case["expected_document"],
                    case["expected_locator"],
                )
            rows.append(row)

    result = {
        "config_id": config_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            **config,
            "max_distance": settings.MAX_DISTANCE,
            "embedding_model": settings.EMBEDDING_MODEL,
            "llm_model": settings.LLM_MODEL,
        },
        "metrics": summarize(rows),
        "cases": rows,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    output = RESULT_DIR / f"{config_id}.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", choices=[*CONFIGS, "all"], default="all")
    args = parser.parse_args()
    targets = list(CONFIGS) if args.config == "all" else [args.config]
    summary_rows = []
    for config_id in targets:
        result = run_one(config_id)
        summary_rows.append({"config_id": config_id, **result["metrics"]})
        print(config_id, json.dumps(result["metrics"], ensure_ascii=False))
    (RESULT_DIR / "summary.json").write_text(
        json.dumps(summary_rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
