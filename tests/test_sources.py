from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from marketpulse.ingestion.sources import (
    RawArticle,
    _strip_html,
    content_hash,
    fetch_edgar,
    fetch_newsapi,
)


def test_content_hash_is_stable_for_same_url():
    h1 = content_hash("https://example.com/article-1")
    h2 = content_hash("https://example.com/article-1")
    assert h1 == h2


def test_content_hash_differs_for_different_urls():
    assert content_hash("https://example.com/a") != content_hash("https://example.com/b")


def test_content_hash_is_hex_sha256_length():
    # sha256 hex digest is exactly 64 chars
    assert len(content_hash("https://example.com/anything")) == 64


def test_raw_article_is_value_equal():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    a = RawArticle(url="u", source="s", title="t", body="b", published_at=now)
    b = RawArticle(url="u", source="s", title="t", body="b", published_at=now)
    assert a == b


def test_raw_article_is_hashable():
    a = RawArticle(url="u", source="s", title="t", body="b", published_at=datetime.now(tz=UTC))
    # frozen=True means hashable — should not raise
    assert isinstance(hash(a), int)


def test_strip_html_removes_tags_but_keeps_text():
    assert _strip_html("<p>hello <b>world</b></p>") == "hello world"


def test_strip_html_handles_empty_string():
    assert _strip_html("") == ""


# ---------------------------------------------------------------------------
# fetch_newsapi
# ---------------------------------------------------------------------------


def test_fetch_newsapi_no_key_yields_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NEWS_API_KEY", raising=False)
    assert list(fetch_newsapi()) == []


def test_fetch_newsapi_explicit_empty_key_yields_nothing() -> None:
    assert list(fetch_newsapi(api_key="")) == []


def test_fetch_newsapi_parses_articles() -> None:
    payload = {
        "articles": [
            {
                "url": "https://example.com/story",
                "title": "Markets surge",
                "description": "Stocks rose sharply.",
                "publishedAt": "2026-05-29T10:00:00Z",
            },
            {
                "url": "https://example.com/removed",
                "title": "[Removed]",
                "description": "",
                "publishedAt": "2026-05-29T09:00:00Z",
            },
        ]
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = payload
    mock_resp.raise_for_status = MagicMock()

    mock_httpx = MagicMock()
    mock_httpx.get.return_value = mock_resp

    with patch.dict("sys.modules", {"httpx": mock_httpx}):
        articles = list(fetch_newsapi(api_key="test-key"))

    assert len(articles) == 1
    assert articles[0].title == "Markets surge"
    assert articles[0].source == "newsapi"
    assert articles[0].body == "Stocks rose sharply."


def test_fetch_newsapi_http_error_yields_nothing() -> None:
    mock_httpx = MagicMock()
    mock_httpx.get.side_effect = Exception("timeout")

    with patch.dict("sys.modules", {"httpx": mock_httpx}):
        articles = list(fetch_newsapi(api_key="test-key"))

    assert articles == []


# ---------------------------------------------------------------------------
# fetch_edgar
# ---------------------------------------------------------------------------


def test_fetch_edgar_parses_hits() -> None:
    payload = {
        "hits": {
            "hits": [
                {
                    "_id": "0000320193-26-000099",
                    "_source": {
                        "entity_name": "APPLE INC",
                        "form_type": "8-K",
                        "file_date": "2026-05-28",
                        "display_names": ["Apple Inc. (AAPL) (CIK 0000320193)"],
                    },
                }
            ]
        }
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = payload
    mock_resp.raise_for_status = MagicMock()
    mock_httpx = MagicMock()
    mock_httpx.get.return_value = mock_resp

    with patch.dict("sys.modules", {"httpx": mock_httpx}):
        articles = list(fetch_edgar(form_type="8-K"))

    assert len(articles) == 1
    assert "APPLE INC" in articles[0].title
    assert articles[0].source == "sec_8k"
    assert "sec.gov" in articles[0].url


def test_fetch_edgar_http_error_yields_nothing() -> None:
    mock_httpx = MagicMock()
    mock_httpx.get.side_effect = Exception("timeout")

    with patch.dict("sys.modules", {"httpx": mock_httpx}):
        articles = list(fetch_edgar())

    assert articles == []


def test_fetch_edgar_10q_source_key() -> None:
    payload = {
        "hits": {
            "hits": [
                {
                    "_id": "0000789019-26-000123",
                    "_source": {
                        "entity_name": "MICROSOFT CORP",
                        "form_type": "10-Q",
                        "file_date": "2026-05-20",
                        "display_names": ["Microsoft Corp (MSFT)"],
                    },
                }
            ]
        }
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = payload
    mock_resp.raise_for_status = MagicMock()
    mock_httpx = MagicMock()
    mock_httpx.get.return_value = mock_resp

    with patch.dict("sys.modules", {"httpx": mock_httpx}):
        articles = list(fetch_edgar(form_type="10-Q"))

    assert articles[0].source == "sec_10q"
