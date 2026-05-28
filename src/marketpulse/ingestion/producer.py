"""Async Kafka producer: polls RSS feeds every POLL_INTERVAL seconds.

Run via: python -m marketpulse.ingestion --mode producer
Requires Kafka reachable at KAFKA_BOOTSTRAP (start with: make kafka-up).
"""

from __future__ import annotations

import asyncio
import json
import logging

from aiokafka import AIOKafkaProducer  # type: ignore[import-untyped]

from .indexer import get_collection
from .pipeline import KAFKA_BOOTSTRAP, POLL_INTERVAL, TOPIC
from .sources import FEEDS, RawArticle, content_hash, fetch_feed

logger = logging.getLogger(__name__)


def article_to_msg(article: RawArticle) -> bytes:
    """Serialise a RawArticle to JSON bytes for the Kafka topic."""
    return json.dumps(
        {
            "url": article.url,
            "source": article.source,
            "title": article.title,
            "body": article.body,
            "published_at": article.published_at.isoformat(),
        }
    ).encode()


def _bootstrap_seen() -> set[str]:
    """Return the set of content hashes already indexed in ChromaDB."""
    try:
        existing = get_collection().get()
        return {id_.rsplit("_", 1)[0] for id_ in (existing["ids"] or [])}
    except Exception as exc:
        logger.warning("could not read ChromaDB for seen-set bootstrap: %s", exc)
        return set()


async def run_producer() -> None:
    """Long-running producer: poll RSS feeds and publish new articles to Kafka."""
    producer: AIOKafkaProducer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)
    await producer.start()

    seen = _bootstrap_seen()
    logger.info("producer started — %d articles already indexed", len(seen))

    try:
        while True:
            published = 0
            for source, url in FEEDS.items():
                try:
                    for article in fetch_feed(source, url):
                        h = content_hash(article.url)
                        if h in seen:
                            continue
                        await producer.send_and_wait(
                            TOPIC,
                            key=h.encode(),
                            value=article_to_msg(article),
                        )
                        seen.add(h)
                        published += 1
                        logger.debug("published %r from %r", article.url, source)
                except Exception as exc:
                    logger.warning("error fetching feed %r: %s", source, exc)

            logger.info("published %d new articles — sleeping %ds", published, POLL_INTERVAL)
            await asyncio.sleep(POLL_INTERVAL)
    finally:
        await producer.stop()
