from app.clients.embeddings import OpenAICompatibleEmbeddingClient
from app.clients.fake import FakeEmbeddingClient, FakeLLMClient
from app.clients.llm import OpenAICompatibleLLMClient
from app.core.config import Settings
from app.core.exceptions import ProviderError


def build_embedding_client(settings: Settings):
    if settings.MODEL_MODE == "fake":
        return FakeEmbeddingClient()
    missing = settings.missing_real_model_config()
    if missing:
        raise ProviderError(f"Missing model config: {', '.join(missing)}")
    return OpenAICompatibleEmbeddingClient(
        endpoint=settings.EMBEDDING_ENDPOINT or "",
        api_key=settings.EMBEDDING_API_KEY or "",
        model=settings.EMBEDDING_MODEL or "",
        timeout_seconds=settings.MODEL_TIMEOUT_SECONDS,
        max_retries=settings.MODEL_MAX_RETRIES,
    )


def build_llm_client(settings: Settings):
    if settings.MODEL_MODE == "fake":
        return FakeLLMClient()
    missing = settings.missing_real_model_config()
    if missing:
        raise ProviderError(f"Missing model config: {', '.join(missing)}")
    return OpenAICompatibleLLMClient(
        endpoint=settings.LLM_ENDPOINT or "",
        api_key=settings.LLM_API_KEY or "",
        model=settings.LLM_MODEL or "",
        timeout_seconds=settings.MODEL_TIMEOUT_SECONDS,
        max_retries=settings.MODEL_MAX_RETRIES,
    )
