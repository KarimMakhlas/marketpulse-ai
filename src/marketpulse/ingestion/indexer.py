"""Chunking, embedding, and ChromaDB upsert. Entry: `run()`."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import chromadb

from ..db import upsert_article
from .sources import FEEDS, RawArticle, content_hash, fetch_feed

logger = logging.getLogger(__name__)

CHROMA_PATH = Path("./data/chroma")
COLLECTION_NAME = "market_news"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

# Lazy module-level singletons. First call instantiates; tests can avoid them
# by only importing the pure helpers (chunk_text, etc.).
_embedder: Any | None = None
_collection: Any | None = None


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping character windows.

    Simple, predictable, dependency-free. For v0.1 this beats a smart splitter:
    news article summaries are short, and embedding models tokenize sub-words
    so a mid-word split costs little retrieval quality.
    """
    if overlap >= chunk_size:
        raise ValueError(f"overlap ({overlap}) must be < chunk_size ({chunk_size})")
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    step = chunk_size - overlap
    chunks: list[str] = []
    for start in range(0, len(text), step):
        chunk = text[start : start + chunk_size]
        chunks.append(chunk)
        if start + chunk_size >= len(text):
            break
    return chunks


def get_embedder() -> Any:
    global _embedder
    if _embedder is None:
        # Deferred import: pulling sentence_transformers triggers a ~1s torch
        # import we don't want to pay during fast unit tests of chunk_text.
        from sentence_transformers import SentenceTransformer

        logger.info("loading embedding model %s", EMBEDDING_MODEL)
        _embedder = SentenceTransformer(EMBEDDING_MODEL)
    return _embedder


def get_collection() -> Any:
    global _collection
    if _collection is None:
        CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        # BGE embeddings are designed for cosine similarity, not Chroma's
        # default L2. Use cosine space; pair with normalize_embeddings=True
        # at encode time for a consistent metric.
        _collection = client.get_or_create_collection(
            COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def upsert_chunks(article: RawArticle, chunks: list[str]) -> int:
    """Embed chunks and upsert into Chroma. Returns chunk count."""
    if not chunks:
        return 0
    embeddings = get_embedder().encode(
        chunks,
        convert_to_numpy=False,
        normalize_embeddings=True,
    )
    # sentence-transformers returns either a Tensor or list-of-lists depending
    # on convert_to_numpy/convert_to_tensor; coerce to plain Python lists.
    embeddings_list = [list(map(float, e)) for e in embeddings]

    article_id = content_hash(article.url)
    ids = [f"{article_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "source": article.source,
            "url": article.url,
            "title": article.title,
            "published_at": article.published_at.isoformat(),
            "chunk_idx": i,
        }
        for i in range(len(chunks))
    ]
    get_collection().upsert(
        ids=ids,
        embeddings=embeddings_list,
        documents=chunks,
        metadatas=metadatas,
    )
    try:
        upsert_article(
            url=article.url,
            source=article.source,
            title=article.title,
            published_at=article.published_at,
            content_hash=content_hash(article.url),
        )
    except Exception as exc:
        logger.warning("db.upsert_article skipped for %r: %s", article.url, exc)
    return len(chunks)


def run() -> tuple[int, int]:
    """Fetch all feeds, chunk, embed, upsert. Returns (articles, chunks)."""
    total_articles = 0
    total_chunks = 0
    for source, url in FEEDS.items():
        logger.info("fetching feed %r", source)
        try:
            articles = list(fetch_feed(source, url))
        except Exception as e:
            logger.warning("failed to fetch %r: %s — skipping", source, e)
            continue
        logger.info("  %d articles from %r", len(articles), source)
        for article in articles:
            text = f"{article.title}. {article.body}".strip()
            chunks = chunk_text(text)
            n = upsert_chunks(article, chunks)
            total_articles += 1
            total_chunks += n
    return total_articles, total_chunks
