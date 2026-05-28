"""Tests for Kafka producer/consumer pure helpers (no network, no Kafka broker)."""

import json
from datetime import UTC, datetime

from marketpulse.ingestion.consumer import msg_to_article
from marketpulse.ingestion.pipeline import CONSUMER_GROUP, KAFKA_BOOTSTRAP, POLL_INTERVAL, TOPIC
from marketpulse.ingestion.producer import article_to_msg
from marketpulse.ingestion.sources import RawArticle

_PUBLISHED = datetime(2026, 5, 28, 10, 0, tzinfo=UTC)

_ARTICLE = RawArticle(
    url="https://ft.com/article/123",
    source="ft.com",
    title="Markets rise",
    body="Stocks climbed on positive data.",
    published_at=_PUBLISHED,
)


# ---------------------------------------------------------------------------
# article_to_msg (producer serialisation)
# ---------------------------------------------------------------------------


def test_article_to_msg_returns_bytes() -> None:
    assert isinstance(article_to_msg(_ARTICLE), bytes)


def test_article_to_msg_is_valid_json() -> None:
    data = json.loads(article_to_msg(_ARTICLE))
    assert isinstance(data, dict)


def test_article_to_msg_contains_all_fields() -> None:
    data = json.loads(article_to_msg(_ARTICLE))
    assert data["url"] == _ARTICLE.url
    assert data["source"] == _ARTICLE.source
    assert data["title"] == _ARTICLE.title
    assert data["body"] == _ARTICLE.body
    assert data["published_at"] == _PUBLISHED.isoformat()


# ---------------------------------------------------------------------------
# msg_to_article (consumer deserialisation)
# ---------------------------------------------------------------------------


def test_msg_to_article_roundtrip() -> None:
    data: dict[str, str] = json.loads(article_to_msg(_ARTICLE))
    recovered = msg_to_article(data)
    assert recovered.url == _ARTICLE.url
    assert recovered.source == _ARTICLE.source
    assert recovered.title == _ARTICLE.title
    assert recovered.body == _ARTICLE.body
    assert recovered.published_at == _ARTICLE.published_at


def test_msg_to_article_preserves_timezone() -> None:
    data: dict[str, str] = json.loads(article_to_msg(_ARTICLE))
    recovered = msg_to_article(data)
    assert recovered.published_at.tzinfo is not None


# ---------------------------------------------------------------------------
# pipeline constants sanity checks
# ---------------------------------------------------------------------------


def test_pipeline_constants_are_set() -> None:
    assert KAFKA_BOOTSTRAP
    assert TOPIC
    assert CONSUMER_GROUP
    assert POLL_INTERVAL > 0


def test_topic_name_is_namespaced() -> None:
    assert "." in TOPIC
