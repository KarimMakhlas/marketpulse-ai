"""CLI entry: `python -m marketpulse.ingestion`.

Runs the end-to-end ingestion + indexing pipeline once and exits.
"""

from __future__ import annotations

import logging
import sys

from .indexer import run


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("marketpulse.ingestion")
    try:
        articles, chunks = run()
    except KeyboardInterrupt:
        log.warning("interrupted")
        return 130
    log.info("done — %d articles, %d chunks upserted", articles, chunks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
