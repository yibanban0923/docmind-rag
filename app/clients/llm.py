from app.clients.http_common import post_json_with_retry


class OpenAICompatibleLLMClient:
    """Concrete HTTP adapter for OpenAI-compatible chat-completions endpoints."""

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

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        data = post_json_with_retry(
            url=self.endpoint,
            api_key=self.api_key,
            payload={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0,
            },
            timeout_seconds=self.timeout_seconds,
            max_retries=self.max_retries,
        )
        return data["choices"][0]["message"]["content"].strip()
