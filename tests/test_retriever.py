import math
from datetime import UTC, datetime, timedelta

from marketpulse.retrieval.retriever import RECENCY_DECAY_RATE, _blend, recency_score


def test_recency_score_for_now_is_one():
    now = datetime.now(tz=UTC)
    assert recency_score(now, now=now) == 1.0


def test_recency_score_7_days_old_matches_formula():
    now = datetime(2026, 5, 27, 12, 0, tzinfo=UTC)
    published = now - timedelta(days=7)
    expected = math.exp(-RECENCY_DECAY_RATE * 7)
    assert recency_score(published, now=now) == expected


def test_recency_score_30_days_old_matches_formula():
    now = datetime(2026, 5, 27, 12, 0, tzinfo=UTC)
    published = now - timedelta(days=30)
    expected = math.exp(-RECENCY_DECAY_RATE * 30)
    assert recency_score(published, now=now) == expected


def test_recency_score_is_monotonically_decreasing():
    now = datetime(2026, 5, 27, 12, 0, tzinfo=UTC)
    scores = [recency_score(now - timedelta(days=d), now=now) for d in range(0, 60, 5)]
    for older, newer in zip(scores[1:], scores[:-1], strict=True):
        assert older <= newer


def test_recency_score_clips_future_dates_to_one():
    now = datetime(2026, 5, 27, 12, 0, tzinfo=UTC)
    future = now + timedelta(days=3)
    # Clock-skewed article should not exceed 1.0 (no bonus for being from the future).
    assert recency_score(future, now=now) == 1.0


def test_blend_pure_similarity_is_seventy_percent():
    assert _blend(similarity=1.0, recency=0.0) == 0.7


def test_blend_pure_recency_is_thirty_percent():
    assert _blend(similarity=0.0, recency=1.0) == 0.3


def test_blend_weights_sum_to_one():
    # both fully on → score = 1.0
    assert _blend(similarity=1.0, recency=1.0) == 1.0
