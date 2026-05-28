"""GeminiProvider — implements LLMProvider against Google's Gemini API.

Uses the modern `google-genai` SDK (the older `google-generativeai` package
is deprecated and its model names — gemini-1.5-* — have been retired).
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-flash-latest"
_MISSING_KEY_MSG = (
    "GEMINI_API_KEY is not set. Either:\n"
    "  1. Copy `.env.example` to `.env` and paste your key, OR\n"
    "  2. `export GEMINI_API_KEY=...` in your shell.\n"
    "Get a free key at https://aistudio.google.com/apikey"
)


class GeminiProvider:
    """Wraps `google-genai` for streaming text generation.

    The SDK import is deferred to first use so tests of unrelated modules
    don't pay the import cost (mirrors the indexer's lazy embedder pattern).
    """

    def __init__(self, model_name: str = DEFAULT_MODEL, api_key: str | None = None) -> None:
        self._model_name = model_name
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self._api_key:
            raise RuntimeError(_MISSING_KEY_MSG)
        self._client: Any | None = None

    def _ensure_client(self) -> Any:
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def generate_stream(self, prompt: str) -> Iterator[str]:
        client = self._ensure_client()
        response = client.models.generate_content_stream(
            model=self._model_name,
            contents=prompt,
        )
        for chunk in response:
            # `.text` can be None on the final empty chunk or a safety-filtered
            # block; skip those quietly so the stream doesn't tear down.
            try:
                token = chunk.text
            except Exception as e:  # noqa: BLE001 — SDK raises bare ValueError sometimes
                logger.warning("skipping non-text chunk: %s", e)
                continue
            if token:
                yield token
