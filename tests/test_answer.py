"""Tests for synthesis/answer.py.

search() now lives in graph/nodes.py, so patches go there.
"""

from unittest.mock import patch

from conftest import FakeProvider, make_chunk
from marketpulse.retrieval.retriever import RetrievedChunk
from marketpulse.synthesis.answer import EMPTY_INDEX_MESSAGE, answer


def _patch_search(chunks: list[RetrievedChunk]):  # type: ignore[no-untyped-def]
    return patch("marketpulse.graph.nodes.search", return_value=chunks)


def test_answer_returns_one_citation_per_retrieved_chunk() -> None:
    chunks = [make_chunk(1), make_chunk(2), make_chunk(3)]
    fake = FakeProvider(tokens=["hello ", "world"])

    with _patch_search(chunks):
        result = answer("any question", provider=fake, k=3)

    assert len(result.citations) == 3


def test_answer_assigns_markers_in_order() -> None:
    chunks = [make_chunk(1), make_chunk(2), make_chunk(3)]

    with _patch_search(chunks):
        result = answer("anything", provider=FakeProvider(tokens=[""]), k=3)

    assert [c.marker for c in result.citations] == ["[S1]", "[S2]", "[S3]"]


def test_answer_passes_through_tokens_unchanged() -> None:
    with _patch_search([make_chunk(1)]):
        fake = FakeProvider(tokens=["foo ", "bar ", "baz"])
        result = answer("anything", provider=fake)
        streamed = "".join(result.tokens)

    assert streamed == "foo bar baz"


def test_answer_prompt_includes_query_and_sources() -> None:
    with _patch_search([make_chunk(7)]):
        fake = FakeProvider(tokens=[""])
        result = answer("MY UNIQUE QUERY", provider=fake)
        list(result.tokens)

    assert fake.last_prompt is not None
    assert "MY UNIQUE QUERY" in fake.last_prompt
    assert "https://example.com/7" in fake.last_prompt


def test_answer_empty_index_returns_synthetic_stream() -> None:
    with _patch_search([]):
        fake = FakeProvider(tokens=["should not appear"])
        result = answer("anything", provider=fake)

    assert result.citations == []
    assert "".join(result.tokens) == EMPTY_INDEX_MESSAGE
    assert fake.last_prompt is None
