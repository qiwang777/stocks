import os
from typing import Any

import httpx


class RationaleService:
    def __init__(
        self,
        client: httpx.Client | None = None,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        base_url: str | None = None,
    ):
        self.api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY") or os.environ.get("SPRING_AI_OPENAI_API_KEY")
        self.model = model or os.environ.get("OPENAI_MODEL") or os.environ.get("SPRING_AI_OPENAI_CHAT_OPTIONS_MODEL") or "gpt-4o-mini"
        self.temperature = temperature if temperature is not None else self._env_float("OPENAI_TEMPERATURE", 0.2)
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self._client = client
        self._owns_client = client is None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=15)
        return self._client

    def explain(self, symbol, horizon, p_up, move, recent):
        if not self.api_key:
            return "Rationale unavailable."
        prompt = (
            "You are a concise market commentary assistant. Given an ML probability "
            f"({p_up}) that next move for {symbol} over horizon {horizon} is {move}, "
            "generate a two-sentence neutral rationale based on generic technical "
            "signals (SMA/RSI/volatility). Do not provide financial advice."
        )
        try:
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "temperature": self.temperature,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            choices = payload.get("choices")
            if not choices:
                return "Rationale unavailable."
            message = choices[0].get("message", {})
            content = message.get("content")
            return content.strip() if isinstance(content, str) and content.strip() else "Rationale unavailable."
        except Exception:
            return "Rationale unavailable."

    def close(self) -> None:
        if self._owns_client and self._client is not None:
            self._client.close()

    def _env_float(self, name: str, default: float) -> float:
        try:
            return float(os.environ.get(name, default))
        except (TypeError, ValueError):
            return default
