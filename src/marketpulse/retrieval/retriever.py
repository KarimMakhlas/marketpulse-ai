"""Search the local Chroma collection by query, blend cosine sim with recency and
source credibility, then re-rank for diversity using Maximal Marginal Relevance."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime

from ..ingestion.indexer import get_collection, get_embedder

DEFAULT_K = 5
N_CANDIDATES_MULTIPLIER = 4  # fetch k*4 candidates so MMR has room to work

# Blend weights (must sum to 1.0)
SIM_WEIGHT = 0.60
RECENCY_WEIGHT = 0.25
CREDIBILITY_WEIGHT = 0.15

RECENCY_DECAY_RATE = 0.1  # exp(-rate * age_days); ~0.5 at 7d, ~0.05 at 30d

MMR_LAMBDA = 0.7  # 0 = max diversity, 1 = pure relevance

# Credibility scores keyed by the source name stored in article metadata.
SOURCE_CREDIBILITY: dict[str, float] = {
    "ft": 1.00,
    "guardian": 0.90,
    "cnbc": 0.85,
    "marketwatch": 0.85,
    "sec_8k": 0.95,  # SEC primary filings — authoritative but dense
    "sec_10q": 0.95,
    "yahoo": 0.80,
    "newsapi": 0.75,
}
DEFAULT_CREDIBILITY = 0.70

# Human-readable names + ingestion kind for each known source key. Used by the
# API's /sources endpoint so the UI lists exactly what the pipeline ingests.
SOURCE_DISPLAY: dict[str, tuple[str, str]] = {
    "ft": ("Financial Times", "rss"),
    "marketwatch": ("MarketWatch", "rss"),
    "yahoo": ("Yahoo Finance", "rss"),
    "cnbc": ("CNBC", "rss"),
    "guardian": ("The Guardian", "rss"),
    "sec_8k": ("SEC EDGAR · 8-K", "edgar"),
    "sec_10q": ("SEC EDGAR · 10-Q", "edgar"),
    "newsapi": ("NewsAPI", "newsapi"),
}


@dataclass(frozen=True)
class SourceInfo:
    id: str
    name: str
    kind: str  # "rss" | "edgar" | "newsapi"
    credibility: float


def list_sources() -> list[SourceInfo]:
    """Return the canonical set of ingestion sources, highest credibility first."""
    infos = [
        SourceInfo(
            id=key,
            name=name,
            kind=kind,
            credibility=SOURCE_CREDIBILITY.get(key, DEFAULT_CREDIBILITY),
        )
        for key, (name, kind) in SOURCE_DISPLAY.items()
    ]
    return sorted(infos, key=lambda s: s.credibility, reverse=True)


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    source: str
    url: str
    title: str
    published_at: datetime
    similarity: float
    recency: float
    credibility: float
    score: float


def recency_score(published_at: datetime, now: datetime | None = None) -> float:
    """Exponential decay on article age. Clipped to [0, 1]."""
    now = now or datetime.now(tz=UTC)
    age_days = (now - published_at).total_seconds() / 86400.0
    # Future-dated articles (clock skew) treated as age=0.
    return math.exp(-RECENCY_DECAY_RATE * max(0.0, age_days))


def credibility_score(source: str) -> float:
    """Return a [0, 1] credibility score for the given source domain."""
    return SOURCE_CREDIBILITY.get(source, DEFAULT_CREDIBILITY)


def _blend(similarity: float, recency: float, credibility: float) -> float:
    return SIM_WEIGHT * similarity + RECENCY_WEIGHT * recency + CREDIBILITY_WEIGHT * credibility


def _dot(a: list[float], b: list[float]) -> float:
    """Dot product of two vectors (valid cosine sim when both are L2-normalised)."""
    return sum(x * y for x, y in zip(a, b, strict=True))


def mmr_rerank(
    chunks: list[RetrievedChunk],
    embeddings: list[list[float]],
    k: int,
    lam: float = MMR_LAMBDA,
) -> list[RetrievedChunk]:
    """Greedy MMR selection from a scored candidate pool.

    Picks k chunks that maximise:
        lam * chunk.score  -  (1-lam) * max_sim(chunk, already_selected)

    chunks and embeddings must be parallel lists of the same length.
    Returns at most k chunks; returns all chunks unchanged if len <= k.
    """
    if len(chunks) <= k:
        return chunks

    selected_indices: list[int] = []
    selected_embeddings: list[list[float]] = []

    while len(selected_indices) < k:
        best_idx = -1
        best_score = float("-inf")

        for i, (chunk, emb) in enumerate(zip(chunks, embeddings, strict=True)):
            if i in selected_indices:
                continue

            redundancy = (
                max(_dot(emb, s) for s in selected_embeddings) if selected_embeddings else 0.0
            )
            mmr_score = lam * chunk.score - (1 - lam) * redundancy

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = i

        selected_indices.append(best_idx)
        selected_embeddings.append(embeddings[best_idx])

    return [chunks[i] for i in selected_indices]


def search(query: str, k: int = DEFAULT_K) -> list[RetrievedChunk]:
    """Embed query, retrieve candidates, score with credibility, MMR re-rank to k."""
    n_candidates = max(k * N_CANDIDATES_MULTIPLIER, 20)

    q_emb = get_embedder().encode(
        [query],
        convert_to_numpy=False,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    q_emb_list = [list(map(float, q_emb[0]))]

    results = get_collection().query(
        query_embeddings=q_emb_list,
        n_results=n_candidates,
        include=["embeddings", "documents", "metadatas", "distances"],
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]
    raw_embeddings: list[list[float]] = results["embeddings"][0]
    now = datetime.now(tz=UTC)

    chunks: list[RetrievedChunk] = []
    for doc, meta, dist, _emb in zip(docs, metas, dists, raw_embeddings, strict=True):
        similarity = max(0.0, 1.0 - float(dist))
        published_at = datetime.fromisoformat(meta["published_at"])
        recency = recency_score(published_at, now=now)
        cred = credibility_score(meta["source"])
        chunks.append(
            RetrievedChunk(
                text=doc,
                source=meta["source"],
                url=meta["url"],
                title=meta["title"],
                published_at=published_at,
                similarity=similarity,
                recency=recency,
                credibility=cred,
                score=_blend(similarity, recency, cred),
            )
        )

    return mmr_rerank(chunks, raw_embeddings, k=k)
