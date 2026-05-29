"""RSS feed configuration, fetch, and the RawArticle dataclass."""

from __future__ import annotations

import hashlib
import logging
import os
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime

import feedparser

logger = logging.getLogger(__name__)

# Free finance/business RSS feeds (no auth required).
FEEDS: dict[str, str] = {
    "ft": "https://www.ft.com/rss/home/international",
    "marketwatch": "http://feeds.marketwatch.com/marketwatch/topstories/",
    "yahoo": "https://finance.yahoo.com/rss/topstories",
    "cnbc": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "guardian": "https://www.theguardian.com/business/rss",
}

_EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
# SEC requires a descriptive User-Agent identifying the application and contact.
_EDGAR_USER_AGENT = "MarketPulseAI research-tool/0.2 contact@marketpulseai.local"

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


_DISPLAY_NAME_SUFFIX = re.compile(r"\s*\(CIK\s+\d+\)\s*$", re.IGNORECASE)


def _entity_from_display_name(display_name: str) -> str:
    """Extract the entity name from an EDGAR display_names entry.

    Format: ``"ENTITY NAME (TICKER) (CIK 000...)"`` — both the CIK suffix and
    the optional ticker parenthetical are stripped so the title reads naturally.
    """
    if not display_name:
        return ""
    name = _DISPLAY_NAME_SUFFIX.sub("", display_name).strip()
    # Drop a trailing "(TICKER)" if present — single token in parens at the end.
    if name.endswith(")"):
        open_idx = name.rfind("(")
        if open_idx > 0 and " " not in name[open_idx + 1 : -1].strip():
            name = name[:open_idx].strip()
    return name


def _parse_published(entry: feedparser.FeedParserDict) -> datetime:
    """Return published time as UTC datetime; fall back to 'now' if absent."""
    tup = entry.get("published_parsed") or entry.get("updated_parsed")
    if tup is None:
        return datetime.now(tz=UTC)
    return datetime(tup[0], tup[1], tup[2], tup[3], tup[4], tup[5], tzinfo=UTC)


_NEWSAPI_BASE = "https://newsapi.org/v2/top-headlines"
_NEWSAPI_SOURCE = "newsapi"


def fetch_newsapi(api_key: str | None = None) -> Iterator[RawArticle]:
    """Yield RawArticle from NewsAPI top business headlines.

    No-op if NEWS_API_KEY is absent. Free tier: 100 req/day, dev use only.
    """
    key = api_key or os.environ.get("NEWS_API_KEY", "")
    if not key:
        logger.debug("NEWS_API_KEY not set — skipping NewsAPI source")
        return

    import httpx

    params = {"category": "business", "language": "en", "pageSize": "20", "apiKey": key}
    try:
        resp = httpx.get(_NEWSAPI_BASE, params=params, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("NewsAPI request failed: %s — skipping", exc)
        return

    for article in data.get("articles", []):
        url = article.get("url")
        title = article.get("title")
        if not url or not title or title == "[Removed]":
            continue
        body = _strip_html(article.get("description") or article.get("content") or "")
        published_raw = article.get("publishedAt", "")
        try:
            published_at = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            published_at = datetime.now(tz=UTC)
        yield RawArticle(
            url=url,
            source=_NEWSAPI_SOURCE,
            title=title,
            body=body,
            published_at=published_at,
        )


def fetch_edgar(
    form_type: str = "8-K", days_back: int = 7, limit: int = 25
) -> Iterator[RawArticle]:
    """Yield RawArticle from recent SEC EDGAR filings via the EFTS JSON API.

    Uses the public EDGAR full-text search index — no API key required.
    SEC requires a User-Agent header; _EDGAR_USER_AGENT satisfies that.
    """
    from datetime import timedelta

    import httpx

    start_date = (datetime.now(tz=UTC) - timedelta(days=days_back)).strftime("%Y-%m-%d")
    params = {
        "q": "",
        "forms": form_type,
        "dateRange": "custom",
        "startdt": start_date,
    }
    try:
        resp = httpx.get(
            _EDGAR_SEARCH_URL,
            params=params,
            headers={"User-Agent": _EDGAR_USER_AGENT},
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("EDGAR fetch failed for %s: %s — skipping", form_type, exc)
        return

    hits = data.get("hits", {}).get("hits", [])[:limit]
    source_key = f"sec_{form_type.lower().replace('-', '')}"

    for hit in hits:
        src = hit.get("_source", {})
        display_names: list[str] = src.get("display_names") or []
        # EFTS exposes the entity inside `display_names` as
        # "ENTITY NAME (TICKER) (CIK 000...)". `entity_name` / `form_type`
        # are not part of this payload, so fall back accordingly.
        entity = (
            src.get("entity_name")
            or _entity_from_display_name(display_names[0] if display_names else "")
            or "Unknown Entity"
        )
        filed_form = src.get("form_type") or src.get("form") or form_type
        file_date: str = src.get("file_date", "")
        # `_id` is "<accession>:<primary-doc-filename>"; `adsh` (when present)
        # is the bare accession. Strip the filename suffix from `_id` as a fallback.
        raw_id: str = hit.get("_id", "")
        accession: str = src.get("adsh") or raw_id.split(":", 1)[0]
        ticker_info = display_names[0] if display_names else entity

        # Build a direct link to the filing index page on SEC.gov.
        if accession:
            cik_raw = accession.split("-")[0].lstrip("0") or "0"
            accession_clean = accession.replace("-", "")
            article_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{cik_raw}/{accession_clean}/{accession}-index.htm"
            )
        else:
            article_url = (
                f"https://www.sec.gov/cgi-bin/browse-edgar"
                f"?action=getcurrent&type={filed_form}&owner=include&count=40"
            )

        try:
            published_at = datetime.fromisoformat(f"{file_date}T00:00:00+00:00")
        except (ValueError, TypeError):
            published_at = datetime.now(tz=UTC)

        body = f"{entity} filed a {filed_form} report with the SEC. {ticker_info}."
        yield RawArticle(
            url=article_url,
            source=source_key,
            title=f"{entity} — {filed_form} Filing",
            body=body,
            published_at=published_at,
        )


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
