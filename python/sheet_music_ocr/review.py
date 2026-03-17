"""LLM-based MusicXML review and correction.

Supports both Claude (Anthropic) and OpenAI APIs for reviewing
MusicXML output from Audiveris and suggesting/applying fixes.
"""

from __future__ import annotations

import enum
import os
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from pathlib import Path

REVIEW_PROMPT = """\
You are a music notation expert. Review the following MusicXML file produced by \
optical music recognition (Audiveris). Look for and fix common OCR errors including:

- Incorrect note pitches or durations
- Wrong or missing key signatures, time signatures, or clefs
- Incorrect rest durations or placements
- Missing or incorrect accidentals
- Wrong beam groupings or tuplets
- Garbled or misspelled lyrics and text annotations
- Missing or incorrect dynamic markings
- Incorrect measure numbers or barline types
- Voice/staff assignment errors

Return ONLY the corrected MusicXML. Do not include any explanation, commentary, or \
markdown formatting. Output the raw XML directly.

Here is the MusicXML to review:

"""

_TIMEOUT = 300


class LLMProvider(enum.StrEnum):
    """Supported LLM providers."""

    CLAUDE = "claude"
    OPENAI = "openai"


class ReviewError(Exception):
    """Raised when LLM review fails."""


def _get_api_key(provider: LLMProvider) -> str:
    env_var = "ANTHROPIC_API_KEY" if provider == LLMProvider.CLAUDE else "OPENAI_API_KEY"
    key = os.environ.get(env_var)
    if not key:
        msg = f"{env_var} environment variable is not set."
        raise ReviewError(msg)
    return key


def _call_claude(content: str, api_key: str) -> str:
    response = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 16384,
            "messages": [{"role": "user", "content": REVIEW_PROMPT + content}],
        },
        timeout=_TIMEOUT,
    )
    if response.status_code != 200:  # noqa: PLR2004
        msg = f"Claude API error ({response.status_code}): {response.text}"
        raise ReviewError(msg)

    data = response.json()
    return data["content"][0]["text"]


def _call_openai(content: str, api_key: str) -> str:
    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": REVIEW_PROMPT + content}],
            "max_tokens": 16384,
        },
        timeout=_TIMEOUT,
    )
    if response.status_code != 200:  # noqa: PLR2004
        msg = f"OpenAI API error ({response.status_code}): {response.text}"
        raise ReviewError(msg)

    data = response.json()
    return data["choices"][0]["message"]["content"]


def review_mxml(mxml_path: Path, provider: LLMProvider) -> str:
    """Review a MusicXML file using an LLM and return corrected content.

    Args:
        mxml_path: Path to the .mxml file to review.
        provider: Which LLM provider to use.

    Returns:
        The corrected MusicXML content as a string.

    Raises:
        ReviewError: If the API call fails or the key is missing.
        FileNotFoundError: If the input file does not exist.
    """
    content = mxml_path.read_text(encoding="utf-8")
    api_key = _get_api_key(provider)

    if provider == LLMProvider.CLAUDE:
        return _call_claude(content, api_key)
    return _call_openai(content, api_key)
