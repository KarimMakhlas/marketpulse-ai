"""Tests for src/marketpulse/db.py — all psycopg2 calls mocked."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

import marketpulse.db as db_client


def _reset_module() -> None:
    """Reset module-level state between tests."""
    db_client._conn = None
    db_client._db_available = False


@pytest.fixture(autouse=True)
def reset_db_state() -> None:
    _reset_module()
    yield  # type: ignore[misc]
    _reset_module()


# ---------------------------------------------------------------------------
# ensure_schema
# ---------------------------------------------------------------------------


def test_ensure_schema_no_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db_client.ensure_schema()
    assert db_client._db_available is False
    assert db_client._conn is None


def test_ensure_schema_empty_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "")
    db_client.ensure_schema()
    assert db_client._db_available is False


def test_ensure_schema_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/marketpulse")
    mock_psycopg2 = MagicMock()
    mock_psycopg2.connect.side_effect = Exception("connection refused")
    with patch.dict("sys.modules", {"psycopg2": mock_psycopg2}):
        db_client.ensure_schema()
    assert db_client._db_available is False
    assert db_client._conn is None


def test_ensure_schema_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/marketpulse")
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_psycopg2 = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn
    with patch.dict("sys.modules", {"psycopg2": mock_psycopg2}):
        db_client.ensure_schema()
    assert db_client._db_available is True
    assert db_client._conn is mock_conn
    mock_cursor.execute.assert_called_once()
    ddl_arg = mock_cursor.execute.call_args[0][0]
    assert "CREATE TABLE IF NOT EXISTS articles" in ddl_arg
    assert "CREATE TABLE IF NOT EXISTS query_log" in ddl_arg


# ---------------------------------------------------------------------------
# upsert_article
# ---------------------------------------------------------------------------


def test_upsert_article_db_unavailable() -> None:
    # _db_available is False by default from fixture — should be a no-op
    db_client.upsert_article(
        url="https://example.com/1",
        source="ft",
        title="Test",
        published_at=datetime.now(tz=UTC),
        content_hash="abc",
    )
    # No exception = pass


def test_upsert_article_executes_sql() -> None:
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    db_client._conn = mock_conn
    db_client._db_available = True

    pub = datetime(2026, 1, 1, tzinfo=UTC)
    db_client.upsert_article(
        url="https://ft.com/article/1",
        source="ft",
        title="A headline",
        published_at=pub,
        content_hash="deadbeef",
    )

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]
    assert "INSERT INTO articles" in sql
    assert "ON CONFLICT" in sql
    assert params[0] == "https://ft.com/article/1"
    assert params[1] == "ft"
    assert params[2] == "A headline"
    assert params[3] == pub
    assert params[5] == "deadbeef"


def test_upsert_article_swallows_exception() -> None:
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("db error")
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    db_client._conn = mock_conn
    db_client._db_available = True

    # Must not raise
    db_client.upsert_article(
        url="https://ft.com/article/x",
        source="ft",
        title="Boom",
        published_at=datetime.now(tz=UTC),
        content_hash="xx",
    )


# ---------------------------------------------------------------------------
# log_query
# ---------------------------------------------------------------------------


def test_log_query_db_unavailable() -> None:
    db_client.log_query("some query", ["https://a.com", "https://b.com"])
    # No exception = pass


def test_log_query_executes_sql() -> None:
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    db_client._conn = mock_conn
    db_client._db_available = True

    urls = ["https://ft.com/1", "https://mw.com/2"]
    db_client.log_query("what happened to markets?", urls)

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]
    assert "INSERT INTO query_log" in sql
    assert params[0] == "what happened to markets?"
    assert params[1] == urls


def test_log_query_swallows_exception() -> None:
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("network gone")
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    db_client._conn = mock_conn
    db_client._db_available = True

    db_client.log_query("crash?", [])  # must not raise


# ---------------------------------------------------------------------------
# count_queries_today / recent_queries
# ---------------------------------------------------------------------------


def test_count_queries_today_db_unavailable() -> None:
    assert db_client.count_queries_today() is None


def test_count_queries_today_returns_int() -> None:
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (7,)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    db_client._conn = mock_conn
    db_client._db_available = True

    assert db_client.count_queries_today() == 7
    sql = mock_cursor.execute.call_args[0][0]
    assert "FROM query_log" in sql


def test_recent_queries_db_unavailable() -> None:
    assert db_client.recent_queries() == []


def test_recent_queries_maps_rows() -> None:
    when = datetime(2026, 5, 30, 12, 0, tzinfo=UTC)
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        ("what about the fed?", "sufficient", when, 5),
        ("swallow velocity?", "insufficient", when, 0),
    ]
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    db_client._conn = mock_conn
    db_client._db_available = True

    rows = db_client.recent_queries(limit=10)
    assert len(rows) == 2
    assert rows[0].query == "what about the fed?"
    assert rows[0].doc_grade == "sufficient"
    assert rows[0].sources_count == 5
    assert rows[1].sources_count == 0
