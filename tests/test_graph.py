"""Tests for the Self-RAG LangGraph pipeline — all LLM and Chroma calls mocked."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import patch

from marketpulse.retrieval.retriever import RetrievedChunk
from marketpulse.synthesis.answer import AnswerStream, _citation_from_chunk

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_chunk(score: float = 0.9, source: str = "ft") -> RetrievedChunk:
    return RetrievedChunk(
        text="Markets rose on strong earnings.",
        source=source,
        url="https://ft.com/article/1",
        title="Markets rise",
        published_at=datetime(2026, 5, 28, tzinfo=UTC),
        similarity=score,
        recency=0.9,
        credibility=1.0,
        score=score,
    )


class FakeLLMProvider:
    """Minimal fake provider — generate() returns a configurable string."""

    def __init__(self, grade_response: str = "SUFFICIENT", stream_text: str = "Answer text.") -> None:
        self._grade_response = grade_response
        self._stream_text = stream_text

    def generate(self, prompt: str) -> str:  # noqa: ARG002
        return self._grade_response

    def generate_stream(self, prompt: str) -> Iterator[str]:  # noqa: ARG002
        yield self._stream_text


# ---------------------------------------------------------------------------
# _citation_from_chunk
# ---------------------------------------------------------------------------

def test_citation_from_chunk_sets_marker() -> None:
    chunk = _make_chunk()
    citation = _citation_from_chunk(1, chunk)
    assert citation.marker == "[S1]"
    assert citation.source == "ft"


def test_citation_from_chunk_excerpt_truncated() -> None:
    long_text = "x" * 200
    chunk = RetrievedChunk(
        text=long_text,
        source="ft",
        url="https://ft.com/1",
        title="T",
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
        similarity=0.9,
        recency=0.9,
        credibility=1.0,
        score=0.9,
    )
    citation = _citation_from_chunk(2, chunk)
    assert len(citation.excerpt) <= 120


# ---------------------------------------------------------------------------
# answer() — mocking search() and provider
# ---------------------------------------------------------------------------

def _mock_search(chunks: list[RetrievedChunk]):  # type: ignore[no-untyped-def]
    return patch("marketpulse.graph.nodes.search", return_value=chunks)


def test_answer_returns_stream_when_sufficient() -> None:
    chunks = [_make_chunk()]
    provider = FakeLLMProvider(grade_response="SUFFICIENT", stream_text="Hello world.")

    with _mock_search(chunks):
        from marketpulse.synthesis.answer import answer
        result = answer("What is the market doing?", provider=provider, k=1)

    assert isinstance(result, AnswerStream)
    assert not result.refused
    assert result.doc_grade == "sufficient"
    assert result.citations


def test_answer_refuses_when_insufficient() -> None:
    chunks = [_make_chunk()]
    provider = FakeLLMProvider(grade_response="INSUFFICIENT")

    with _mock_search(chunks):
        from marketpulse.synthesis.answer import answer
        result = answer("What is the velocity of a swallow?", provider=provider, k=1)

    assert result.refused
    assert result.doc_grade == "insufficient"
    tokens = "".join(result.tokens)
    assert len(tokens) > 0  # refusal message present


def test_answer_returns_empty_index_message_when_no_chunks() -> None:
    provider = FakeLLMProvider()

    with _mock_search([]):
        from marketpulse.synthesis.answer import answer
        result = answer("any query", provider=provider, k=5)

    assert not result.refused
    assert not result.citations
    tokens = "".join(result.tokens)
    assert "ingest" in tokens.lower()


def test_answer_streams_tokens_when_sufficient() -> None:
    chunks = [_make_chunk()]
    provider = FakeLLMProvider(grade_response="SUFFICIENT", stream_text="token1")

    with _mock_search(chunks):
        from marketpulse.synthesis.answer import answer
        result = answer("earnings news?", provider=provider, k=1)

    tokens = list(result.tokens)
    assert "token1" in tokens


# ---------------------------------------------------------------------------
# grade_docs_node
# ---------------------------------------------------------------------------

def test_grade_docs_node_sufficient() -> None:
    from marketpulse.graph.nodes import grade_docs_node
    from marketpulse.graph.state import GraphState

    state: GraphState = {
        "query": "What happened to markets?",
        "k": 1,
        "chunks": [_make_chunk()],
        "citations": [],
        "doc_grade": "",
        "prompt": "",
        "refused": False,
        "refusal_reason": "",
    }
    provider = FakeLLMProvider(grade_response="SUFFICIENT")
    result = grade_docs_node(state, provider=provider)
    assert result["doc_grade"] == "sufficient"


def test_grade_docs_node_insufficient() -> None:
    from marketpulse.graph.nodes import grade_docs_node
    from marketpulse.graph.state import GraphState

    state: GraphState = {
        "query": "swallow velocity?",
        "k": 1,
        "chunks": [_make_chunk()],
        "citations": [],
        "doc_grade": "",
        "prompt": "",
        "refused": False,
        "refusal_reason": "",
    }
    provider = FakeLLMProvider(grade_response="INSUFFICIENT")
    result = grade_docs_node(state, provider=provider)
    assert result["doc_grade"] == "insufficient"


def test_grade_docs_node_empty_chunks_returns_insufficient() -> None:
    from marketpulse.graph.nodes import grade_docs_node
    from marketpulse.graph.state import GraphState

    state: GraphState = {
        "query": "any",
        "k": 5,
        "chunks": [],
        "citations": [],
        "doc_grade": "",
        "prompt": "",
        "refused": False,
        "refusal_reason": "",
    }
    provider = FakeLLMProvider()
    result = grade_docs_node(state, provider=provider)
    assert result["doc_grade"] == "insufficient"
    assert result["refused"] is True


# ---------------------------------------------------------------------------
# route_after_grading
# ---------------------------------------------------------------------------

def test_route_sufficient() -> None:
    from marketpulse.graph.nodes import route_after_grading
    from marketpulse.graph.state import GraphState

    state: GraphState = {
        "query": "q",
        "k": 1,
        "chunks": [],
        "citations": [],
        "doc_grade": "sufficient",
        "prompt": "",
        "refused": False,
        "refusal_reason": "",
    }
    assert route_after_grading(state) == "build_prompt"


def test_route_insufficient() -> None:
    from marketpulse.graph.nodes import route_after_grading
    from marketpulse.graph.state import GraphState

    state: GraphState = {
        "query": "q",
        "k": 1,
        "chunks": [],
        "citations": [],
        "doc_grade": "insufficient",
        "prompt": "",
        "refused": False,
        "refusal_reason": "",
    }
    assert route_after_grading(state) == "refuse"
