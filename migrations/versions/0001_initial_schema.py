"""initial schema: articles, query_log, alerts, users

Revision ID: 0001
Revises:
Create Date: 2026-05-29

Mirrors the DDL in src/marketpulse/db.py so a fresh deployment can be
provisioned with `alembic upgrade head` instead of relying on ensure_schema().
ensure_schema() remains for zero-setup local dev; Alembic is the production path.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "articles",
        sa.Column("url", sa.Text, primary_key=True),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("ingested_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("content_hash", sa.Text, nullable=False),
    )
    op.create_table(
        "query_log",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("chunk_urls", sa.ARRAY(sa.Text), nullable=False),
        sa.Column("doc_grade", sa.Text, nullable=False, server_default=""),
        sa.Column("queried_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("alert_type", sa.Text, nullable=False),
        sa.Column("detail", sa.Text, nullable=False, server_default=""),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.Text, nullable=False, unique=True),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("users")
    op.drop_table("alerts")
    op.drop_table("query_log")
    op.drop_table("articles")
