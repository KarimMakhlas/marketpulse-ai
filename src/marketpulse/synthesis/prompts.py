"""Prompt templates and source formatting for the synthesis LLM call."""

from __future__ import annotations

from ..retrieval.retriever import RetrievedChunk

MAX_EXCERPT_CHARS = 600  # per source, in the prompt

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


def format_sources(chunks: list[RetrievedChunk]) -> str:
    """Render chunks as numbered [S1], [S2], ... blocks for the prompt."""
    blocks: list[str] = []
    for i, c in enumerate(chunks, start=1):
        date = c.published_at.strftime("%Y-%m-%d")
        excerpt = c.text[:MAX_EXCERPT_CHARS]
        blocks.append(f'[S{i}] {c.source}, {date}, {c.url}\n"{excerpt}"')
    return "\n\n".join(blocks)


def build_prompt(query: str, chunks: list[RetrievedChunk]) -> str:
    return (
        SYSTEM_INSTRUCTION
        + "\n\n"
        + USER_PROMPT_TEMPLATE.format(query=query, sources_block=format_sources(chunks))
    )
