"""Search the local Chroma collection by query, blend cosine sim with recency."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime

from ..ingestion.indexer import get_collection, get_embedder

DEFAULT_K = 5
SIM_WEIGHT = 0.7
RECENCY_WEIGHT = 0.3
RECENCY_DECAY_RATE = 0.1  # exp(-rate * age_days); ~0.5 at 7d, ~0.05 at 30d


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    source: str
    url: str
    title: str
    published_at: datetime
    similarity: float
    recency: float
    score: float


def recency_score(published_at: datetime, now: datetime | None = None) -> float:
    """Exponential decay on article age. Clipped to [0, 1]."""
    now = now or datetime.now(tz=UTC)
    age_days = (now - published_at).total_seconds() / 86400.0
    # Future-dated articles (clock skew) treated as age=0.
    return math.exp(-RECENCY_DECAY_RATE * max(0.0, age_days))


def _blend(similarity: float, recency: float) -> float:
    return SIM_WEIGHT * similarity + RECENCY_WEIGHT * recency


def search(query: str, k: int = DEFAULT_K) -> list[RetrievedChunk]:
    """Embed `query`, retrieve top-k chunks, re-sort by blended score."""
    q_emb = get_embedder().encode(
        [query],
        convert_to_numpy=False,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    q_emb_list = [list(map(float, q_emb[0]))]

    results = get_collection().query(query_embeddings=q_emb_list, n_results=k)

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]
    now = datetime.now(tz=UTC)

    chunks: list[RetrievedChunk] = []
    for doc, meta, dist in zip(docs, metas, dists, strict=True):
        # Chroma cosine distance ∈ [0, 2]; sim = 1 - dist ∈ [-1, 1]; clip neg.
        similarity = max(0.0, 1.0 - float(dist))
        published_at = datetime.fromisoformat(meta["published_at"])
        recency = recency_score(published_at, now=now)
        chunks.append(
            RetrievedChunk(
                text=doc,
                source=meta["source"],
                url=meta["url"],
                title=meta["title"],
                published_at=published_at,
                similarity=similarity,
                recency=recency,
                score=_blend(similarity, recency),
            )
        )
    return sorted(chunks, key=lambda c: c.score, reverse=True)
