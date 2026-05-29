"""Postgres persistence layer — articles table + query audit log."""

from .client import ensure_schema, log_query, upsert_article

__all__ = ["ensure_schema", "log_query", "upsert_article"]
