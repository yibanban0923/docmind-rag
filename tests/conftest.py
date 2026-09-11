from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.clients.fake import FakeEmbeddingClient, FakeLLMClient
from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        APP_ENV="test",
        MODEL_MODE="fake",
        DATA_DIR=tmp_path / "data",
        CHUNK_SIZE=120,
        CHUNK_OVERLAP=20,
        TOP_K=3,
        MAX_DISTANCE=1.0,
        CONTEXT_MAX_CHARS=1200,
    )


@pytest.fixture
def fake_embedding() -> FakeEmbeddingClient:
    return FakeEmbeddingClient()


@pytest.fixture
def fake_llm() -> FakeLLMClient:
    return FakeLLMClient()


@pytest.fixture
def app(test_settings, fake_embedding, fake_llm):
    return create_app(
        settings=test_settings,
        embedding_client=fake_embedding,
        llm_client=fake_llm,
    )


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client
