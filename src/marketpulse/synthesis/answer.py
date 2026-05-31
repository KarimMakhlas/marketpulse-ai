"""Answer orchestration and prompt templates for the Self-RAG pipeline."""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..db import log_alert, log_query
from ..llm.provider import LLMProvider
from ..observability import observe as _lf_observe
from ..retrieval.retriever import DEFAULT_K, RetrievedChunk

logger = logging.getLogger(__name__)

EMPTY_INDEX_MESSAGE = "No indexed sources to answer from. Run `make ingest` first."

# ---------------------------------------------------------------------------
# Prompt templates (merged from synthesis/prompts.py)
# ---------------------------------------------------------------------------

MAX_EXCERPT_CHARS = 600

SYSTEM_INSTRUCTION = "You are a precise financial analyst assistant."

USER_PROMPT_TEMPLATE = """Use ONLY the sources below to answer the question.
Cite each factual claim inline with [S1], [S2], etc. matching the source
numbers below.

If the sources do not answer the question, say so explicitly. Do NOT
extrapolate beyond what the sources state. Do NOT invent citation numbers
that are not in the source list.

Question: {query}

Sources:
{sources_block}

Answer (concise, citation-rich, max ~200 words):
"""

GRADE_DOCS_TEMPLATE = """You are grading document relevance for a financial news assistant.

Query: {query}

Retrieved document excerpts:
{sources_block}

Do any of these documents contain information that is relevant to the query topic?
Answer SUFFICIENT if at least one document covers the topic, even partially.
Answer INSUFFICIENT only if the documents are entirely unrelated to the query (e.g. a sports question in a financial news index).
Reply with exactly one word: SUFFICIENT or INSUFFICIENT."""

GRADE_ANSWER_TEMPLATE = """You are grading answer groundedness.

Question: {query}

Sources provided:
{sources_block}

Answer given:
{answer}

Does the answer rely only on the provided sources without inventing facts not present in them?
Reply with exactly one word: GROUNDED or HALLUCINATION."""


def format_sources(chunks: list[RetrievedChunk]) -> str:
    """Render chunks as numbered [S1], [S2], ... blocks for the prompt."""
    blocks: list[str] = []
    for i, c in enumerate(chunks, start=1):
        date = c.published_at.strftime("%Y-%m-%d")
        excerpt = c.text[:MAX_EXCERPT_CHARS]
        blocks.append(f'[S{i}] {c.source}, {date}, {c.url}\n"{excerpt}"')
    return "\n\n".join(blocks)


def build_grade_docs_prompt(query: str, chunks: list[RetrievedChunk]) -> str:
    return GRADE_DOCS_TEMPLATE.format(
        query=query,
        sources_block=format_sources(chunks),
    )


def build_grade_answer_prompt(query: str, chunks: list[RetrievedChunk], answer: str) -> str:
    return GRADE_ANSWER_TEMPLATE.format(
        query=query,
        sources_block=format_sources(chunks),
        answer=answer,
    )


def build_prompt(query: str, chunks: list[RetrievedChunk]) -> str:
    return (
        SYSTEM_INSTRUCTION
        + "\n\n"
        + USER_PROMPT_TEMPLATE.format(query=query, sources_block=format_sources(chunks))
    )


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
    refused: bool = False  # True when Self-RAG grader rejected the docs
    doc_grade: str = ""  # "sufficient" | "insufficient" | ""


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


@_lf_observe
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
