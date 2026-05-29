"""Tests for synthesis/answer.py.

search() now lives in graph/nodes.py, so patches go there.
FakeLLM must implement both generate_stream() and generate().
"""

from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import patch

from marketpulse.retrieval.retriever import RetrievedChunk
from marketpulse.synthesis.answer import EMPTY_INDEX_MESSAGE, answer


class FakeLLM:
    def __init__(self, tokens: list[str], grade: str = "SUFFICIENT") -> None:
        self._tokens = tokens
        self._grade = grade
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:  # noqa: ARG002
        return self._grade

    def generate_stream(self, prompt: str) -> Iterator[str]:
        self.last_prompt = prompt
        yield from self._tokens


def _chunk(i: int) -> RetrievedChunk:
    return RetrievedChunk(
        text=f"text {i}",
        source=f"src{i}",
        url=f"https://example.com/{i}",
        title=f"Title {i}",
        published_at=datetime(2026, 5, 27, tzinfo=UTC),
        similarity=0.5,
        recency=0.5,
        credibility=0.85,
        score=0.5,
    )


def _patch_search(chunks: list[RetrievedChunk]):  # type: ignore[no-untyped-def]
    return patch("marketpulse.graph.nodes.search", return_value=chunks)


def test_answer_returns_one_citation_per_retrieved_chunk() -> None:
    chunks = [_chunk(1), _chunk(2), _chunk(3)]
    fake = FakeLLM(tokens=["hello ", "world"])

    with _patch_search(chunks):
        result = answer("any question", provider=fake, k=3)

    assert len(result.citations) == 3


def test_answer_assigns_markers_in_order() -> None:
    chunks = [_chunk(1), _chunk(2), _chunk(3)]

    with _patch_search(chunks):
        result = answer("anything", provider=FakeLLM(tokens=[""]), k=3)

    assert [c.marker for c in result.citations] == ["[S1]", "[S2]", "[S3]"]


def test_answer_passes_through_tokens_unchanged() -> None:
    with _patch_search([_chunk(1)]):
        fake = FakeLLM(tokens=["foo ", "bar ", "baz"])
        result = answer("anything", provider=fake)
        streamed = "".join(result.tokens)

    assert streamed == "foo bar baz"


def test_answer_prompt_includes_query_and_sources() -> None:
    with _patch_search([_chunk(7)]):
        fake = FakeLLM(tokens=[""])
        result = answer("MY UNIQUE QUERY", provider=fake)
        list(result.tokens)

    assert fake.last_prompt is not None
    assert "MY UNIQUE QUERY" in fake.last_prompt
    assert "https://example.com/7" in fake.last_prompt


def test_answer_empty_index_returns_synthetic_stream() -> None:
    with _patch_search([]):
        fake = FakeLLM(tokens=["should not appear"])
        result = answer("anything", provider=fake)

    assert result.citations == []
    assert "".join(result.tokens) == EMPTY_INDEX_MESSAGE
    assert fake.last_prompt is None
