#!/usr/bin/env bash
# Full local CI simulation: format check → lint → typecheck → test.
# Mirrors what CI would run. Does NOT run ingest (requires network + disk).
set -euo pipefail

cd "$(dirname "$0")/.."

echo ""
echo "=============================="
echo " MarketPulseAI Local CI"
echo "=============================="
echo ""

echo "[1/4] Format check (ruff format --check)"
uv run ruff format --check src/ tests/
echo "      OK"

echo ""
echo "[2/4] Lint (ruff check)"
uv run ruff check src/ tests/
echo "      OK"

echo ""
echo "[3/4] Type check (mypy --strict)"
uv run mypy --strict src/marketpulse/
echo "      OK"

echo ""
echo "[4/4] Tests (pytest)"
uv run pytest --tb=short -q
echo "      OK"

echo ""
echo "=============================="
echo " All checks passed."
echo "=============================="
