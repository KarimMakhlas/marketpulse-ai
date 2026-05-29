"""Answer orchestration: Self-RAG graph → grade docs → stream or refuse."""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..db import log_alert, log_query
from ..llm.provider import LLMProvider
from ..retrieval.retriever import DEFAULT_K, RetrievedChunk

logger = logging.getLogger(__name__)

EMPTY_INDEX_MESSAGE = "No indexed sources to answer from. Run `make ingest` first."

# Langfuse @observe — transparent no-op when credentials are absent.
try:
    from langfuse.decorators import observe as _lf_observe
except ImportError:
    def _lf_observe(func: Any = None, **_: Any) -> Any:
        return func if func is not None else (lambda f: f)


@dataclass(frozen=True)
class Citation:
    marker: str  # "[S1]", "[S2]", ...
    source: str
    title: str
    url: str
    published_at: datetime
    excerpt: str  # first ~120 chars
    similarity: float
    recency: float
    score: float


@dataclass(frozen=True)
class AnswerStream:
    citations: list[Citation]     # known up-front, before any token streams
    tokens: Iterator[str]
    refused: bool = False         # True when Self-RAG grader rejected the docs
    doc_grade: str = ""           # "sufficient" | "insufficient" | ""


def _citation_from_chunk(i: int, chunk: RetrievedChunk) -> Citation:
    return Citation(
        marker=f"[S{i}]",
        source=chunk.source,
        title=chunk.title,
        url=chunk.url,
        published_at=chunk.published_at,
        excerpt=chunk.text[:120],
        similarity=chunk.similarity,
        recency=chunk.recency,
        score=chunk.score,
    )


@_lf_observe  # type: ignore[untyped-decorator]
def answer(query: str, *, provider: LLMProvider, k: int = DEFAULT_K) -> AnswerStream:
    """Run the Self-RAG graph, then stream the LLM answer (or return a refusal)."""
    # Lazy import to avoid circular dependency at module load time.
    from ..graph.build import build_graph

    graph = build_graph(provider)
    thread_id = hashlib.sha256(query.encode()).hexdigest()[:16]
    config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "query": query,
        "k": k,
        "grade_chunks": [],
        "chunks": [],
        "citations": [],
        "doc_grade": "",
        "prompt": "",
        "refused": False,
        "refusal_reason": "",
    }

    result = graph.invoke(initial_state, config=config)

    chunks: list[RetrievedChunk] = result.get("chunks", [])
    citations: list[Citation] = result.get("citations", [])
    doc_grade: str = result.get("doc_grade", "")
    refused: bool = result.get("refused", False)
    prompt: str = result.get("prompt", "")

    # No chunks at all — index is empty.
    if not chunks:
        return AnswerStream(
            citations=[],
            tokens=iter([EMPTY_INDEX_MESSAGE]),
            refused=False,
            doc_grade="",
        )

    # Grader decided sources are insufficient.
    if refused or not prompt:
        refusal_msg = result.get("refusal_reason", EMPTY_INDEX_MESSAGE)
        log_alert(query, "insufficient_sources", doc_grade)
        return AnswerStream(
            citations=citations,
            tokens=iter([refusal_msg]),
            refused=True,
            doc_grade=doc_grade,
        )

    log_query(query, [c.url for c in chunks], doc_grade=doc_grade)
    return AnswerStream(
        citations=citations,
        tokens=provider.generate_stream(prompt),
        refused=False,
        doc_grade=doc_grade,
    )
