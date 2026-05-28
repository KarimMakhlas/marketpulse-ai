"""Async Kafka consumer: reads raw articles, embeds, upserts to ChromaDB.

Run via: python -m marketpulse.ingestion --mode consumer
Requires Kafka reachable at KAFKA_BOOTSTRAP (start with: make kafka-up).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from aiokafka import AIOKafkaConsumer  # type: ignore[import-untyped]

from .indexer import chunk_text, upsert_chunks
from .pipeline import CONSUMER_GROUP, KAFKA_BOOTSTRAP, TOPIC
from .sources import RawArticle

logger = logging.getLogger(__name__)


def msg_to_article(data: dict[str, str]) -> RawArticle:
    """Deserialise a Kafka message payload into a RawArticle."""
    return RawArticle(
        url=data["url"],
        source=data["source"],
        title=data["title"],
        body=data["body"],
        published_at=datetime.fromisoformat(data["published_at"]),
    )


async def run_consumer() -> None:
    """Long-running consumer: read articles from Kafka, embed, upsert to ChromaDB."""
    consumer: AIOKafkaConsumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=CONSUMER_GROUP,
        auto_offset_reset="earliest",
    )
    await consumer.start()
    logger.info("consumer started — listening on topic %r", TOPIC)

    try:
        async for msg in consumer:
            try:
                data: dict[str, str] = json.loads(msg.value)
                article = msg_to_article(data)
                text = f"{article.title}. {article.body}".strip()
                chunks = chunk_text(text)
                n = upsert_chunks(article, chunks)
                logger.info("indexed %d chunks from %r (%r)", n, article.url, article.source)
            except Exception as exc:
                logger.error("failed to process message offset=%d: %s", msg.offset, exc)
    finally:
        await consumer.stop()
