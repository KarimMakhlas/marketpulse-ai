"""Pydantic request/response models for the API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from ..retrieval.retriever import DEFAULT_K
from ..synthesis.answer import Citation


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: int
    username: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    k: int = Field(default=DEFAULT_K, ge=1, le=10)


class CitationOut(BaseModel):
    marker: str
    source: str
    title: str
    url: str
    published_at: datetime
    excerpt: str
    similarity: float
    recency: float
    score: float

    @classmethod
    def from_citation(cls, c: Citation) -> CitationOut:
        return cls(
            marker=c.marker,
            source=c.source,
            title=c.title,
            url=c.url,
            published_at=c.published_at,
            excerpt=c.excerpt,
            similarity=c.similarity,
            recency=c.recency,
            score=c.score,
        )


class QueryResponse(BaseModel):
    answer: str
    refused: bool
    doc_grade: str
    citations: list[CitationOut]


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    model: str
    default_k: int
    db: bool
    redis: bool


class StatsResponse(BaseModel):
    articles_indexed: int | None  # None when Chroma is unreachable
    queries_today: int | None  # None when Postgres is unavailable
    sources_active: int
    db_available: bool


class QueryLogOut(BaseModel):
    query: str
    doc_grade: str
    queried_at: datetime
    sources_count: int


class SourceOut(BaseModel):
    id: str
    name: str
    kind: str
    credibility: float
