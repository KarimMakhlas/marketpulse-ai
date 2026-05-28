#!/usr/bin/env bash
# Format all Python source files with ruff.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> ruff format"
uv run ruff format src/ tests/

echo "==> ruff check --fix"
uv run ruff check --fix src/ tests/

echo "==> formatting done"
