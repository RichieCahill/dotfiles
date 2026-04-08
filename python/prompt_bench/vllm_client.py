"""OpenAI-compatible client for vLLM's API."""

from __future__ import annotations

import logging
import time
from typing import Self

import httpx

logger = logging.getLogger(__name__)

READY_POLL_INTERVAL = 2.0


class VLLMClient:
    """Talk to a vLLM server via its OpenAI-compatible API.

    Args:
        host: vLLM host.
        port: vLLM port.
        timeout: Per-request timeout in seconds.
    """

    def __init__(self, *, host: str = "localhost", port: int = 8000, timeout: int = 300) -> None:
        """Create a client connected to a vLLM server."""
        self._client = httpx.Client(base_url=f"http://{host}:{port}", timeout=timeout)

    def wait_ready(self, max_wait: int) -> None:
        """Poll /v1/models until the server is ready or timeout."""
        deadline = time.monotonic() + max_wait
        while time.monotonic() < deadline:
            try:
                response = self._client.get("/v1/models")
                if response.is_success:
                    logger.info("vLLM server is ready")
                    return
            except httpx.TransportError:
                pass
            time.sleep(READY_POLL_INTERVAL)
        msg = f"vLLM server not ready after {max_wait}s"
        raise TimeoutError(msg)

    def complete(self, prompt: str, model: str, *, temperature: float = 0.0, max_tokens: int = 4096) -> str:
        """Send a prompt to /v1/completions and return the response text."""
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        logger.info("Sending prompt to %s (%d chars)", model, len(prompt))
        response = self._client.post("/v1/completions", json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["text"]

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> Self:
        """Enter the context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """Close the HTTP client on exit."""
        self.close()
