"""Flexible LLM client for ollama backends."""

from __future__ import annotations

import base64
import logging
from typing import Any, Self

import httpx

logger = logging.getLogger(__name__)


class LLMClient:
    """Talk to an ollama instance.

    Args:
        model: Ollama model name.
        host: Ollama host.
        port: Ollama port.
        temperature: Sampling temperature.
    """

    def __init__(self, model: str, host: str, port: int = 11434, *, temperature: float = 0.1) -> None:
        self.model = model
        self.temperature = temperature
        self._client = httpx.Client(base_url=f"http://{host}:{port}", timeout=120)

    def chat(self, prompt: str, image_data: bytes | None = None, system: str | None = None) -> str:
        """Send a text prompt and return the response."""
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})

        user_msg = {"role": "user", "content": prompt}
        if image_data:
            user_msg["images"] = [base64.b64encode(image_data).decode()]

        messages.append(user_msg)
        return self._generate(messages)

    def _generate(self, messages: list[dict[str, Any]]) -> str:
        """Call the ollama chat API."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        logger.info(f"LLM request to {self.model}")
        response = self._client.post("/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]

    def list_models(self) -> list[str]:
        """List available models on the ollama instance."""
        response = self._client.get("/api/tags")
        response.raise_for_status()
        return [m["name"] for m in response.json().get("models", [])]

    def __enter__(self) -> Self:
        """Enter the context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """Close the HTTP client on exit."""
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
