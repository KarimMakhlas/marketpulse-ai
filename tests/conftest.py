"""Shared test helpers — FakeProvider and make_chunk used across all test modules."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

from marketpulse.retrieval.retriever import RetrievedChunk


class FakeProvider:
    """Minimal LLMProvider fake with configurable grade and token output."""

    def __init__(self, tokens: list[str] | None = None, grade: str = "SUFFICIENT") -> None:
        self._tokens = tokens if tokens is not None else ["test answer"]
        self._grade = grade
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:  # noqa: ARG002
        return self._grade

    def generate_stream(self, prompt: str) -> Iterator[str]:
        self.last_prompt = prompt
        yield from self._tokens


def make_chunk(
    i: int = 1,
    *,
    text: str = "body text",
    source: str = "ft",
    score: float = 0.9,
) -> RetrievedChunk:
    return RetrievedChunk(
        text=text,
        source=source,
        url=f"https://example.com/{i}",
        title=f"Title {i}",
        published_at=datetime(2026, 5, 27, tzinfo=UTC),
        similarity=score,
        recency=0.9,
        credibility=1.0,
        score=score,
    )
