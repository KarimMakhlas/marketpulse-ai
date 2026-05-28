"""CLI: `python -m marketpulse.retrieval "your query" [--k 5]`."""

from __future__ import annotations

import argparse
import logging
import sys

from .retriever import DEFAULT_K, search


def main() -> int:
    parser = argparse.ArgumentParser(prog="marketpulse.retrieval")
    parser.add_argument("query", help="Natural-language query")
    parser.add_argument("--k", type=int, default=DEFAULT_K, help=f"top-k (default {DEFAULT_K})")
    args = parser.parse_args()

    # Quiet by default — the user wants results, not progress bars.
    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    chunks = search(args.query, k=args.k)
    if not chunks:
        print("(no chunks indexed — run `make ingest` first)")
        return 0

    for rank, c in enumerate(chunks, start=1):
        published = c.published_at.strftime("%Y-%m-%d %H:%M")
        preview = c.text[:120].replace("\n", " ")
        print(f"#{rank}  score={c.score:.3f}  (sim={c.similarity:.2f}  rec={c.recency:.2f})")
        print(f"     {c.source:>11s} | {published} | {c.title}")
        print(f"     {c.url}")
        print(f"     {preview}…")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
