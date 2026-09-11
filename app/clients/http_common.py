import time
from typing import Any

import httpx

from app.core.exceptions import ProviderError, ProviderTimeoutError


def post_json_with_retry(
    *,
    url: str,
    api_key: str,
    payload: dict[str, Any],
    timeout_seconds: float,
    max_retries: int,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    attempts = max(1, max_retries)
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            with httpx.Client(timeout=timeout_seconds) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as exc:
            last_error = exc
            if attempt == attempts - 1:
                raise ProviderTimeoutError() from exc
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
            if attempt == attempts - 1:
                raise ProviderError() from exc
        time.sleep(0.5 * (attempt + 1))
    raise ProviderError() from last_error
