#!/usr/bin/env bash
# Run all quality checks: lint, typecheck, test.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> lint"
make lint

echo "==> typecheck"
make typecheck

echo "==> test"
make test

echo "==> all checks passed"
