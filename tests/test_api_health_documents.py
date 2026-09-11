

def test_live(client):
    assert client.get("/health/live").status_code == 200


def test_ready_fake_mode(client):
    response = client.get("/health/ready")
    assert response.status_code == 200


def test_upload_markdown_and_list(client):
    response = client.post(
        "/documents",
        files={"file": ("note.md", b"# Intro\nFastAPI is a web framework.", "text/markdown")},
    )
    assert response.status_code == 201
    document_id = response.json()["document_id"]
    assert response.json()["chunk_count"] >= 1
    assert client.get("/documents").json()["items"][0]["document_id"] == document_id
    assert client.get(f"/documents/{document_id}").status_code == 200


def test_duplicate_upload_returns_409(client):
    files = {"file": ("note.md", b"same content", "text/markdown")}
    assert client.post("/documents", files=files).status_code == 201
    files = {"file": ("copy.md", b"same content", "text/markdown")}
    assert client.post("/documents", files=files).status_code == 409


def test_unsupported_extension_returns_422(client):
    response = client.post("/documents", files={"file": ("a.txt", b"hello", "text/plain")})
    assert response.status_code == 422


def test_empty_file_returns_422(client):
    response = client.post("/documents", files={"file": ("a.md", b"", "text/markdown")})
    assert response.status_code == 422


def test_get_missing_document_returns_404(client):
    assert client.get("/documents/missing").status_code == 404
