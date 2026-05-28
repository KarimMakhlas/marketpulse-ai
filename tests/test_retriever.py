import math
from datetime import UTC, datetime, timedelta

import pytest

from marketpulse.retrieval.retriever import (
    DEFAULT_CREDIBILITY,
    RECENCY_DECAY_RATE,
    SOURCE_CREDIBILITY,
    RetrievedChunk,
    _blend,
    _dot,
    credibility_score,
    mmr_rerank,
    recency_score,
)

# ---------------------------------------------------------------------------
# recency_score
# ---------------------------------------------------------------------------


def test_recency_score_for_now_is_one() -> None:
    now = datetime.now(tz=UTC)
    assert recency_score(now, now=now) == 1.0


def test_recency_score_7_days_old_matches_formula() -> None:
    now = datetime(2026, 5, 27, 12, 0, tzinfo=UTC)
    published = now - timedelta(days=7)
    expected = math.exp(-RECENCY_DECAY_RATE * 7)
    assert recency_score(published, now=now) == expected


def test_recency_score_30_days_old_matches_formula() -> None:
    now = datetime(2026, 5, 27, 12, 0, tzinfo=UTC)
    published = now - timedelta(days=30)
    expected = math.exp(-RECENCY_DECAY_RATE * 30)
    assert recency_score(published, now=now) == expected


def test_recency_score_is_monotonically_decreasing() -> None:
    now = datetime(2026, 5, 27, 12, 0, tzinfo=UTC)
    scores = [recency_score(now - timedelta(days=d), now=now) for d in range(0, 60, 5)]
    for older, newer in zip(scores[1:], scores[:-1], strict=True):
        assert older <= newer


def test_recency_score_clips_future_dates_to_one() -> None:
    now = datetime(2026, 5, 27, 12, 0, tzinfo=UTC)
    future = now + timedelta(days=3)
    assert recency_score(future, now=now) == 1.0


# ---------------------------------------------------------------------------
# credibility_score
# ---------------------------------------------------------------------------


def test_credibility_score_ft() -> None:
    assert credibility_score("ft.com") == SOURCE_CREDIBILITY["ft.com"]


def test_credibility_score_marketwatch() -> None:
    assert credibility_score("marketwatch.com") == SOURCE_CREDIBILITY["marketwatch.com"]


def test_credibility_score_ft_is_highest() -> None:
    assert credibility_score("ft.com") >= credibility_score("marketwatch.com")


def test_credibility_score_unknown_source_returns_default() -> None:
    assert credibility_score("unknown-blog.example.com") == DEFAULT_CREDIBILITY


def test_credibility_score_all_known_sources_above_default() -> None:
    for source, score in SOURCE_CREDIBILITY.items():
        assert score >= DEFAULT_CREDIBILITY, f"{source} credibility below default"


# ---------------------------------------------------------------------------
# _blend
# ---------------------------------------------------------------------------


def test_blend_all_ones_is_one() -> None:
    assert _blend(similarity=1.0, recency=1.0, credibility=1.0) == pytest.approx(1.0)


def test_blend_all_zeros_is_zero() -> None:
    assert _blend(similarity=0.0, recency=0.0, credibility=0.0) == 0.0


def test_blend_only_similarity() -> None:
    result = _blend(similarity=1.0, recency=0.0, credibility=0.0)
    assert result == pytest.approx(0.60)


def test_blend_only_recency() -> None:
    result = _blend(similarity=0.0, recency=1.0, credibility=0.0)
    assert result == pytest.approx(0.25)


def test_blend_only_credibility() -> None:
    result = _blend(similarity=0.0, recency=0.0, credibility=1.0)
    assert result == pytest.approx(0.15)


# ---------------------------------------------------------------------------
# _dot
# ---------------------------------------------------------------------------


def test_dot_orthogonal_vectors_is_zero() -> None:
    assert _dot([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_dot_identical_unit_vectors_is_one() -> None:
    assert _dot([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# mmr_rerank
# ---------------------------------------------------------------------------


def _make_chunk(score: float, source: str = "ft.com") -> RetrievedChunk:
    return RetrievedChunk(
        text="text",
        source=source,
        url="https://example.com",
        title="title",
        published_at=datetime(2026, 5, 27, tzinfo=UTC),
        similarity=score,
        recency=1.0,
        credibility=1.0,
        score=score,
    )


def test_mmr_rerank_returns_k_items() -> None:
    chunks = [_make_chunk(1.0 - i * 0.1) for i in range(10)]
    embeddings = [[1.0, 0.0] if i == 0 else [0.0, 1.0] for i in range(10)]
    result = mmr_rerank(chunks, embeddings, k=3)
    assert len(result) == 3


def test_mmr_rerank_fewer_than_k_returns_all() -> None:
    chunks = [_make_chunk(0.9), _make_chunk(0.8)]
    embeddings = [[1.0, 0.0], [0.0, 1.0]]
    result = mmr_rerank(chunks, embeddings, k=5)
    assert len(result) == 2


def test_mmr_rerank_exact_k_returns_all() -> None:
    chunks = [_make_chunk(0.9), _make_chunk(0.8), _make_chunk(0.7)]
    embeddings = [[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]]
    result = mmr_rerank(chunks, embeddings, k=3)
    assert len(result) == 3


def test_mmr_rerank_prefers_diverse_over_redundant() -> None:
    # chunk A: high score, embedding [1, 0]
    # chunk B: medium score, embedding [0.99, 0.14]  — nearly identical to A
    # chunk C: lower score, embedding [0, 1]  — orthogonal to A
    # With lam=0.7, after selecting A, B should lose to C (redundancy penalty)
    chunk_a = _make_chunk(1.0)
    chunk_b = _make_chunk(0.9)
    chunk_c = _make_chunk(0.7)
    emb_a = [1.0, 0.0]
    emb_b = [0.99, 0.14]  # nearly parallel to A
    emb_c = [0.0, 1.0]  # orthogonal to A

    result = mmr_rerank([chunk_a, chunk_b, chunk_c], [emb_a, emb_b, emb_c], k=2, lam=0.7)
    assert len(result) == 2
    assert result[0] is chunk_a
    assert result[1] is chunk_c  # diverse beats redundant


def test_mmr_pure_relevance_lambda_preserves_score_order() -> None:
    chunks = [_make_chunk(1.0 - i * 0.1) for i in range(5)]
    # all same embedding → redundancy equal for all; pure score ordering
    embeddings = [[1.0, 0.0]] * 5
    result = mmr_rerank(chunks, embeddings, k=3, lam=1.0)
    scores = [c.score for c in result]
    assert scores == sorted(scores, reverse=True)
