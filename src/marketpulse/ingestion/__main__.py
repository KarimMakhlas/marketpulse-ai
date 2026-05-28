"""CLI entry: `python -m marketpulse.ingestion`.

Modes:
  --mode once      (default) Run ingestion once and exit — no Kafka needed.
  --mode producer  Long-running async RSS poller that publishes to Kafka.
  --mode consumer  Long-running async consumer that embeds and upserts to ChromaDB.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="marketpulse.ingestion")
    parser.add_argument(
        "--mode",
        choices=["once", "producer", "consumer"],
        default="once",
        help=(
            "once: run ingestion once and exit (default, no Kafka required); "
            "producer: continuous RSS poll → Kafka; "
            "consumer: Kafka → embed → ChromaDB"
        ),
    )
    args = parser.parse_args()
    _setup_logging()
    log = logging.getLogger("marketpulse.ingestion")

    if args.mode == "once":
        from .indexer import run

        try:
            articles, chunks = run()
        except KeyboardInterrupt:
            log.warning("interrupted")
            return 130
        log.info("done — %d articles, %d chunks upserted", articles, chunks)
        return 0

    if args.mode == "producer":
        from .producer import run_producer

        log.info("starting Kafka producer (Ctrl-C to stop)")
        try:
            asyncio.run(run_producer())
        except KeyboardInterrupt:
            log.info("producer stopped")
        return 0

    if args.mode == "consumer":
        from .consumer import run_consumer

        log.info("starting Kafka consumer (Ctrl-C to stop)")
        try:
            asyncio.run(run_consumer())
        except KeyboardInterrupt:
            log.info("consumer stopped")
        return 0

    return 0  # unreachable — argparse validates choices


if __name__ == "__main__":
    sys.exit(main())
