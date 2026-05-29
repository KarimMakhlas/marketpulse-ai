"""LangGraph node functions for the Self-RAG pipeline.

Each node takes GraphState and returns a dict of fields to merge back.
Langfuse @observe() wraps the grader nodes when credentials are set;
it is a transparent no-op otherwise.
"""

from __future__ import annotations

import logging
from typing import Any

from ..llm.provider import LLMProvider
from ..retrieval.retriever import RetrievedChunk, search
from ..synthesis.answer import _citation_from_chunk
from ..synthesis.prompts import build_grade_docs_prompt, build_prompt
from .state import GraphState

logger = logging.getLogger(__name__)

_REFUSAL_MESSAGE = (
    "The indexed sources do not contain sufficient information to answer this question. "
    "Try re-running `make ingest` to refresh the index, or rephrase your question."
)

# Langfuse @observe is a transparent no-op when credentials are absent.
try:
    from langfuse.decorators import observe as _lf_observe
except ImportError:
    def _lf_observe(func: Any = None, **_: Any) -> Any:
        return func if func is not None else (lambda f: f)


def retrieve_node(state: GraphState, *, provider: LLMProvider) -> dict[str, Any]:  # noqa: ARG001
    """Retrieve top-k chunks from Chroma and format citations."""
    chunks: list[RetrievedChunk] = search(state["query"], k=state["k"])
    citations = [_citation_from_chunk(i, c) for i, c in enumerate(chunks, start=1)]
    return {"chunks": chunks, "citations": citations}


@_lf_observe  # type: ignore[untyped-decorator]
def grade_docs_node(state: GraphState, *, provider: LLMProvider) -> dict[str, Any]:
    """Ask the LLM whether the retrieved docs are sufficient to answer the query."""
    chunks = state["chunks"]
    if not chunks:
        return {"doc_grade": "insufficient", "refused": True, "refusal_reason": _REFUSAL_MESSAGE}

    prompt = build_grade_docs_prompt(state["query"], chunks)
    raw = provider.generate(prompt).strip().upper()
    # Check INSUFFICIENT before SUFFICIENT — the latter is a substring of the former.
    if "INSUFFICIENT" in raw:
        grade = "insufficient"
    elif "SUFFICIENT" in raw:
        grade = "sufficient"
    else:
        grade = "insufficient"  # default to safe/refuse on unexpected output
    logger.info("doc grade: %s (raw=%r)", grade, raw[:40])
    return {"doc_grade": grade}


def build_prompt_node(state: GraphState, *, provider: LLMProvider) -> dict[str, Any]:  # noqa: ARG001
    """Build the synthesis prompt (no LLM call — just formats state into a prompt)."""
    prompt = build_prompt(state["query"], state["chunks"])
    return {"prompt": prompt, "refused": False, "refusal_reason": ""}


def refuse_node(state: GraphState, *, provider: LLMProvider) -> dict[str, Any]:  # noqa: ARG001
    """Set the refusal flag when grading deems docs insufficient."""
    return {
        "refused": True,
        "refusal_reason": _REFUSAL_MESSAGE,
        "prompt": "",
    }


def route_after_grading(state: GraphState) -> str:
    """Conditional edge: sufficient → build_prompt, insufficient → refuse."""
    return "build_prompt" if state["doc_grade"] == "sufficient" else "refuse"
