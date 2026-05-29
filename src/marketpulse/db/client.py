"""Postgres connection management, schema DDL, and write helpers.

DATABASE_URL env var (e.g. postgresql://localhost/marketpulse) controls
connectivity. If the var is absent or the connection fails at startup,
all public functions become no-ops so the ingestion and synthesis paths
keep working without a running database.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import psycopg2  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

# Module-level connection; None means "DB unavailable — skip quietly".
_conn: psycopg2.connection | None = None
_db_available: bool = False

_DDL = """
CREATE TABLE IF NOT EXISTS articles (
    url          TEXT        PRIMARY KEY,
    source       TEXT        NOT NULL,
    title        TEXT        NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    ingested_at  TIMESTAMPTZ NOT NULL,
    content_hash TEXT        NOT NULL
);

CREATE TABLE IF NOT EXISTS query_log (
    id          SERIAL      PRIMARY KEY,
    query       TEXT        NOT NULL,
    chunk_urls  TEXT[]      NOT NULL,
    doc_grade   TEXT        NOT NULL DEFAULT '',
    queried_at  TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id          SERIAL      PRIMARY KEY,
    query       TEXT        NOT NULL,
    alert_type  TEXT        NOT NULL,
    detail      TEXT        NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL
);
"""


def _get_conn() -> psycopg2.connection | None:
    return _conn


def ensure_schema() -> None:
    """Create tables if they don't exist. No-op if DB is unavailable."""
    global _conn, _db_available

    url = os.environ.get("DATABASE_URL", "")
    if not url:
        logger.debug("DATABASE_URL not set — Postgres integration disabled")
        return

    try:
        import psycopg2

        _conn = psycopg2.connect(url)
        _conn.autocommit = True
        with _conn.cursor() as cur:
            cur.execute(_DDL)
        _db_available = True
        logger.info("Postgres schema ready")
    except Exception as exc:
        logger.warning("Postgres unavailable (%s) — DB writes disabled", exc)
        _conn = None
        _db_available = False


def upsert_article(
    url: str,
    source: str,
    title: str,
    published_at: datetime,
    content_hash: str,
) -> None:
    """Insert or update an article row. No-op if DB is unavailable."""
    if not _db_available or _conn is None:
        return
    sql = """
        INSERT INTO articles (url, source, title, published_at, ingested_at, content_hash)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO UPDATE
            SET title        = EXCLUDED.title,
                published_at = EXCLUDED.published_at,
                ingested_at  = EXCLUDED.ingested_at,
                content_hash = EXCLUDED.content_hash;
    """
    try:
        with _conn.cursor() as cur:
            cur.execute(
                sql,
                (url, source, title, published_at, datetime.now(tz=UTC), content_hash),
            )
    except Exception as exc:
        logger.warning("upsert_article failed for %r: %s", url, exc)


def log_query(query: str, chunk_urls: list[str], doc_grade: str = "") -> None:
    """Write a query audit row. No-op if DB is unavailable."""
    if not _db_available or _conn is None:
        return
    sql = """
        INSERT INTO query_log (query, chunk_urls, doc_grade, queried_at)
        VALUES (%s, %s, %s, %s);
    """
    try:
        with _conn.cursor() as cur:
            cur.execute(sql, (query, chunk_urls, doc_grade, datetime.now(tz=UTC)))
    except Exception as exc:
        logger.warning("log_query failed: %s", exc)


def log_alert(query: str, alert_type: str, detail: str = "") -> None:
    """Write an alert row (e.g. insufficient sources, quality drift). No-op if DB unavailable."""
    if not _db_available or _conn is None:
        return
    sql = """
        INSERT INTO alerts (query, alert_type, detail, created_at)
        VALUES (%s, %s, %s, %s);
    """
    try:
        with _conn.cursor() as cur:
            cur.execute(sql, (query, alert_type, detail, datetime.now(tz=UTC)))
    except Exception as exc:
        logger.warning("log_alert failed: %s", exc)
