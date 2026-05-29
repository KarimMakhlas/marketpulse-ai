"""LLMProvider Protocol — the only contract synthesis depends on.

Any class with a `generate_stream(prompt) -> Iterator[str]` method satisfies it
structurally (no inheritance needed). This is what makes swapping providers a
one-line change.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol


class LLMProvider(Protocol):
    def generate_stream(self, prompt: str) -> Iterator[str]: ...
    def generate(self, prompt: str) -> str: ...
