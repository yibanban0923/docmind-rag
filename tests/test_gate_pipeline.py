from app.clients.fake import FakeLLMClient
from app.rag.gate import REFUSAL_TEXT


def test_gate_refusal_does_not_call_llm(app, client, fake_llm: FakeLLMClient):
    app.state.container.rag_pipeline.max_distance = -1.0
    response = client.post("/ask", json={"question": "unrelated"})
    assert response.status_code == 200
    assert response.json()["answer"] == REFUSAL_TEXT
    assert fake_llm.call_count == 0


def test_unknown_source_from_model_is_rejected(app, client, fake_llm: FakeLLMClient):
    client.post("/documents", files={"file": ("note.md", b"# A\nhello world", "text/markdown")})
    fake_llm.response = "bad answer [S9]"
    app.state.container.rag_pipeline.max_distance = 2.0
    response = client.post("/ask", json={"question": "hello"})
    assert response.status_code == 502
    assert response.json()["code"] == "MODEL_OUTPUT_INVALID"
