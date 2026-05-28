#!/usr/bin/env bash
# Run pytest, passing through any extra arguments.
# Examples:
#   ./scripts/test.sh
#   ./scripts/test.sh -v
#   ./scripts/test.sh -k "chunk"
#   ./scripts/test.sh tests/test_retriever.py -v
set -euo pipefail

cd "$(dirname "$0")/.."

uv run pytest "$@"
