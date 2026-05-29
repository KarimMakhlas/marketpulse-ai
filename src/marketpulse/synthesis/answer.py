"""Answer orchestration: retrieve → build prompt → stream LLM tokens."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime

from ..db import log_query
from ..llm.provider import LLMProvider
from ..retrieval.retriever import DEFAULT_K, RetrievedChunk, search
from .prompts import build_prompt

EMPTY_INDEX_MESSAGE = "No indexed sources to answer from. Run `make ingest` first."


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
    citations: list[Citation]  # known up-front, before any token streams
    tokens: Iterator[str]


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


def answer(query: str, *, provider: LLMProvider, k: int = DEFAULT_K) -> AnswerStream:
    """Retrieve top-k chunks, format prompt, stream the LLM's answer."""
    chunks = search(query, k=k)
    if not chunks:
        return AnswerStream(citations=[], tokens=iter([EMPTY_INDEX_MESSAGE]))

    citations = [_citation_from_chunk(i, c) for i, c in enumerate(chunks, start=1)]
    log_query(query, [c.url for c in chunks])
    prompt = build_prompt(query, chunks)
    return AnswerStream(citations=citations, tokens=provider.generate_stream(prompt))
