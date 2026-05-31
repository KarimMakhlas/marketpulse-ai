"""Shared Kafka configuration for producer and consumer."""

from __future__ import annotations

KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC = "marketpulse.raw-articles"
CONSUMER_GROUP = "marketpulse-indexer"
POLL_INTERVAL = 300  # seconds between RSS polls in the producer
