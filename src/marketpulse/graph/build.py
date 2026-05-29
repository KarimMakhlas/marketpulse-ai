"""Assemble the Self-RAG LangGraph pipeline.

Graph:  retrieve → grade_docs → (route) → build_prompt | refuse → END

The compiled graph is cached at module level so it's only built once.
"""

from __future__ import annotations

import functools
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from ..llm.provider import LLMProvider
from .nodes import (
    build_prompt_node,
    grade_docs_node,
    refuse_node,
    retrieve_node,
    route_after_grading,
)
from .state import GraphState

_memory = MemorySaver()


def _bind(node_fn: Any, provider: LLMProvider) -> Any:
    """Return a LangGraph-compatible node that has `provider` pre-bound."""
    return functools.partial(node_fn, provider=provider)


def build_graph(provider: LLMProvider) -> Any:
    """Build and compile the Self-RAG StateGraph for a given provider."""
    builder: StateGraph[GraphState] = StateGraph(GraphState)

    builder.add_node("retrieve", _bind(retrieve_node, provider))
    builder.add_node("grade_docs", _bind(grade_docs_node, provider))
    builder.add_node("build_prompt", _bind(build_prompt_node, provider))
    builder.add_node("refuse", _bind(refuse_node, provider))

    builder.set_entry_point("retrieve")
    builder.add_edge("retrieve", "grade_docs")
    builder.add_conditional_edges(
        "grade_docs",
        route_after_grading,
        {"build_prompt": "build_prompt", "refuse": "refuse"},
    )
    builder.add_edge("build_prompt", END)
    builder.add_edge("refuse", END)

    return builder.compile(checkpointer=_memory)
