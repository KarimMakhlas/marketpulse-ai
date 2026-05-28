"""RSS feed configuration, fetch, and the RawArticle dataclass."""

from __future__ import annotations

import hashlib
import logging
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime

import feedparser

logger = logging.getLogger(__name__)

# Two free finance/business feeds confirmed reachable as of v0.1.
# Reuters' public RSS was discontinued — substituted MarketWatch.
FEEDS: dict[str, str] = {
    "ft": "https://www.ft.com/rss/home/international",
    "marketwatch": "http://feeds.marketwatch.com/marketwatch/topstories/",
}

_HTML_TAG = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class RawArticle:
    url: str
    source: str
    title: str
    body: str
    published_at: datetime


def content_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def _strip_html(text: str) -> str:
    return _HTML_TAG.sub("", text).strip()


def _parse_published(entry: feedparser.FeedParserDict) -> datetime:
    """Return published time as UTC datetime; fall back to 'now' if absent."""
    tup = entry.get("published_parsed") or entry.get("updated_parsed")
    if tup is None:
        return datetime.now(tz=UTC)
    return datetime(tup[0], tup[1], tup[2], tup[3], tup[4], tup[5], tzinfo=UTC)


def fetch_feed(source: str, url: str) -> Iterator[RawArticle]:
    """Yield RawArticle for each well-formed entry in the feed.

    Entries missing a link or title are skipped (logged at DEBUG).
    Network errors propagate up — caller decides whether to continue.
    """
    parsed = feedparser.parse(url)
    if parsed.bozo and not parsed.entries:
        logger.warning("feed %r returned no entries (bozo=%s)", source, parsed.bozo_exception)
        return

    for entry in parsed.entries:
        link = entry.get("link")
        title = entry.get("title")
        if not link or not title:
            logger.debug("skipping malformed entry in %r: missing link/title", source)
            continue

        body = _strip_html(entry.get("summary", entry.get("description", "")))
        yield RawArticle(
            url=link,
            source=source,
            title=title,
            body=body,
            published_at=_parse_published(entry),
        )
