import hashlib
import math
import re


class FakeEmbeddingClient:
    """Deterministic local embedding for tests/CI; not for quality evaluation."""

    def __init__(self, dimensions: int = 64):
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


class FakeLLMClient:
    def __init__(self, response: str = "根据提供的资料，可以确认该信息。[S1]"):
        self.response = response
        self.call_count = 0

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.call_count += 1
        return self.response
