"""Postgres persistence layer — articles, query audit log, alerts, and users."""

from .client import (
    DBUnavailableError,
    UserAlreadyExistsError,
    UserRecord,
    create_user,
    db_available,
    ensure_schema,
    get_user,
    log_alert,
    log_query,
    upsert_article,
)

__all__ = [
    "DBUnavailableError",
    "UserAlreadyExistsError",
    "UserRecord",
    "create_user",
    "db_available",
    "ensure_schema",
    "get_user",
    "log_alert",
    "log_query",
    "upsert_article",
]
