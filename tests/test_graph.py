"""Tests for the Self-RAG LangGraph pipeline — all LLM and Chroma calls mocked."""

from __future__ import annotations

from unittest.mock import patch

from conftest import FakeProvider, make_chunk
from marketpulse.retrieval.retriever import RetrievedChunk
from marketpulse.synthesis.answer import AnswerStream, _citation_from_chunk

# ---------------------------------------------------------------------------
# _citation_from_chunk
# ---------------------------------------------------------------------------


def test_citation_from_chunk_sets_marker() -> None:
    chunk = make_chunk()
    citation = _citation_from_chunk(1, chunk)
    assert citation.marker == "[S1]"
    assert citation.source == "ft"


def test_citation_from_chunk_excerpt_truncated() -> None:
    long_text = "x" * 200
    chunk = make_chunk(2, text=long_text)
    citation = _citation_from_chunk(2, chunk)
    assert len(citation.excerpt) <= 120


# ---------------------------------------------------------------------------
# answer() — mocking search() and provider
# ---------------------------------------------------------------------------


def _mock_search(chunks: list[RetrievedChunk]):  # type: ignore[no-untyped-def]
    return patch("marketpulse.graph.nodes.search", return_value=chunks)


def test_answer_returns_stream_when_sufficient() -> None:
    chunks = [make_chunk()]
    provider = FakeProvider(tokens=["Hello world."], grade="SUFFICIENT")

    with _mock_search(chunks):
        from marketpulse.synthesis.answer import answer

        result = answer("What is the market doing?", provider=provider, k=1)

    assert isinstance(result, AnswerStream)
    assert not result.refused
    assert result.doc_grade == "sufficient"
    assert result.citations


def test_answer_refuses_when_insufficient() -> None:
    chunks = [make_chunk()]
    provider = FakeProvider(grade="INSUFFICIENT")

    with _mock_search(chunks):
        from marketpulse.synthesis.answer import answer

        result = answer("What is the velocity of a swallow?", provider=provider, k=1)

    assert result.refused
    assert result.doc_grade == "insufficient"
    tokens = "".join(result.tokens)
    assert len(tokens) > 0  # refusal message present


def test_answer_returns_empty_index_message_when_no_chunks() -> None:
    provider = FakeProvider()

    with _mock_search([]):
        from marketpulse.synthesis.answer import answer

        result = answer("any query", provider=provider, k=5)

    assert not result.refused
    assert not result.citations
    tokens = "".join(result.tokens)
    assert "ingest" in tokens.lower()


def test_answer_streams_tokens_when_sufficient() -> None:
    chunks = [make_chunk()]
    provider = FakeProvider(tokens=["token1"], grade="SUFFICIENT")

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
        "chunks": [make_chunk()],
        "citations": [],
        "doc_grade": "",
        "prompt": "",
        "refused": False,
        "refusal_reason": "",
    }
    provider = FakeProvider(grade="SUFFICIENT")
    result = grade_docs_node(state, provider=provider)
    assert result["doc_grade"] == "sufficient"


def test_grade_docs_node_insufficient() -> None:
    from marketpulse.graph.nodes import grade_docs_node
    from marketpulse.graph.state import GraphState

    state: GraphState = {
        "query": "swallow velocity?",
        "k": 1,
        "chunks": [make_chunk()],
        "citations": [],
        "doc_grade": "",
        "prompt": "",
        "refused": False,
        "refusal_reason": "",
    }
    provider = FakeProvider(grade="INSUFFICIENT")
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
    provider = FakeProvider()
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
