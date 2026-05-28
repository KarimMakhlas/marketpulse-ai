from datetime import UTC, datetime

from marketpulse.ingestion.sources import RawArticle, _strip_html, content_hash


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
