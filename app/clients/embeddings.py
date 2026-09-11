from app.clients.http_common import post_json_with_retry


class OpenAICompatibleEmbeddingClient:
    """Concrete HTTP adapter for OpenAI-compatible embedding endpoints."""

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        max_retries: int,
    ):
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def _embed(self, texts: list[str]) -> list[list[float]]:
        data = post_json_with_retry(
            url=self.endpoint,
            api_key=self.api_key,
            payload={"model": self.model, "input": texts},
            timeout_seconds=self.timeout_seconds,
            max_retries=self.max_retries,
        )
        rows = sorted(data["data"], key=lambda item: item.get("index", 0))
        return [row["embedding"] for row in rows]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]
