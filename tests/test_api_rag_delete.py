

def upload(client, text=b"# Python\nFastAPI supports dependency injection."):
    response = client.post("/documents", files={"file": ("note.md", text, "text/markdown")})
    assert response.status_code == 201
    return response.json()["document_id"]


def test_retrieve_returns_metadata(client):
    upload(client)
    response = client.post("/retrieve", json={"question": "FastAPI dependency injection"})
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["rank"] == 1
    assert "distance" in item
    assert item["section"] == "Python"


def test_ask_returns_sources(client):
    upload(client)
    response = client.post("/ask", json={"question": "What does FastAPI support?"})
    assert response.status_code == 200
    body = response.json()
    assert body["sources"][0]["source_id"] == "S1"
    assert "request_id" in body


def test_delete_removes_vectors_and_metadata(client):
    document_id = upload(client)
    assert client.delete(f"/documents/{document_id}").status_code == 204
    assert client.get(f"/documents/{document_id}").status_code == 404
    response = client.post("/retrieve", json={"question": "FastAPI dependency injection"})
    assert response.json()["items"] == []


def test_delete_missing_returns_404(client):
    assert client.delete("/documents/missing").status_code == 404


def test_invalid_question_returns_422(client):
    assert client.post("/ask", json={"question": ""}).status_code == 422
