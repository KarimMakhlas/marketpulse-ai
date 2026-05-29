"""Postgres connection management, schema DDL, and write helpers.

DATABASE_URL env var (e.g. postgresql://localhost/marketpulse) controls
connectivity. If the var is absent or the connection fails at startup,
all public functions become no-ops so the ingestion and synthesis paths
keep working without a running database.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import psycopg2  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

# Module-level connection; None means "DB unavailable — skip quietly".
_conn: psycopg2.connection | None = None
_db_available: bool = False


class DBUnavailableError(RuntimeError):
    """Raised by auth paths when a database is required but not reachable.

    Audit writes (articles, query_log, alerts) degrade to no-ops when the DB is
    down, but authentication cannot: a login with no user store must fail loudly
    rather than silently succeed or reject.
    """


class UserAlreadyExistsError(ValueError):
    """Raised when registering a username that already exists."""


@dataclass(frozen=True)
class UserRecord:
    id: int
    username: str
    password_hash: str


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

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL      PRIMARY KEY,
    username      TEXT        UNIQUE NOT NULL,
    password_hash TEXT        NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL
);

-- Idempotent column adds for tables created before v0.3 introduced doc_grade.
-- CREATE TABLE IF NOT EXISTS skips when the table already exists, so new
-- columns must be added explicitly. ADD COLUMN IF NOT EXISTS is Postgres 9.6+.
ALTER TABLE query_log ADD COLUMN IF NOT EXISTS doc_grade TEXT NOT NULL DEFAULT '';
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


def db_available() -> bool:
    """True when a live Postgres connection is established."""
    return _db_available and _conn is not None


def create_user(username: str, password_hash: str) -> UserRecord:
    """Insert a new user. Auth-critical — raises instead of no-op'ing.

    Raises:
        DBUnavailableError: no database connection is available.
        UserAlreadyExistsError: the username is already taken.
    """
    if not _db_available or _conn is None:
        raise DBUnavailableError("user store unavailable — set DATABASE_URL")
    sql = """
        INSERT INTO users (username, password_hash, created_at)
        VALUES (%s, %s, %s)
        RETURNING id;
    """
    try:
        with _conn.cursor() as cur:
            cur.execute(sql, (username, password_hash, datetime.now(tz=UTC)))
            row = cur.fetchone()
    except Exception as exc:
        # psycopg2.errors.UniqueViolation subclasses Exception; detect by message
        # to avoid importing the driver at module top level (kept lazy elsewhere).
        if "duplicate key" in str(exc).lower() or "unique" in str(exc).lower():
            raise UserAlreadyExistsError(username) from exc
        raise
    if row is None:  # pragma: no cover - RETURNING always yields a row on success
        raise DBUnavailableError("user insert returned no id")
    return UserRecord(id=int(row[0]), username=username, password_hash=password_hash)


def get_user(username: str) -> UserRecord | None:
    """Fetch a user by username, or None if absent. No-op-safe when DB is down."""
    if not _db_available or _conn is None:
        return None
    sql = "SELECT id, username, password_hash FROM users WHERE username = %s;"
    try:
        with _conn.cursor() as cur:
            cur.execute(sql, (username,))
            row = cur.fetchone()
    except Exception as exc:
        logger.warning("get_user failed for %r: %s", username, exc)
        return None
    if row is None:
        return None
    return UserRecord(id=int(row[0]), username=str(row[1]), password_hash=str(row[2]))


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
