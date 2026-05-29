"""LangGraph state schema for the Self-RAG pipeline."""

from __future__ import annotations

from typing import Literal, TypedDict

from ..retrieval.retriever import RetrievedChunk
from ..synthesis.answer import Citation


class GraphState(TypedDict):
    query: str
    k: int
    chunks: list[RetrievedChunk]
    citations: list[Citation]
    doc_grade: Literal["sufficient", "insufficient", ""]
    prompt: str          # formatted synthesis prompt, set by build_prompt node
    refused: bool
    refusal_reason: str
