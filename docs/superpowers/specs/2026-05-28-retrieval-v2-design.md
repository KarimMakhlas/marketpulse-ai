# Design: Retrieval v0.2 — MMR Re-ranking + Source Credibility

**Date:** 2026-05-28
**Status:** Approved
**Scope:** `src/marketpulse/retrieval/retriever.py` + `tests/test_retriever.py` only

---

## Problem

The v0.1 retriever returns the top-5 chunks by `0.7·cosine + 0.3·recency`. Two issues:

1. **Redundancy:** chunks 2–5 often cover the same angle as chunk 1 (same article, same paragraph reworded). The LLM synthesizes a narrower answer than the index actually supports.
2. **No source quality signal:** a low-credibility source ranks the same as a high-credibility one given equal cosine similarity.

---

## Solution

Two changes to `retriever.py`, no new infra or dependencies:

### 1. MMR re-ranking (Maximal Marginal Relevance)

Retrieve a larger candidate pool (top-20), then greedily select the final top-k by maximising:

```
mmr(c) = λ · score(c)  −  (1−λ) · max_sim(c, already_selected)
```

- `score(c)` is the blended relevance score (cosine + recency + credibility)
- `max_sim(c, already_selected)` is the max dot-product between chunk `c`'s embedding and all already-selected chunks' embeddings (works because embeddings are already L2-normalised)
- `λ = 0.7` — strong relevance preference with meaningful diversity enforcement

Requires fetching raw embeddings from ChromaDB (`include=["embeddings", ...]`).

### 2. Source credibility weighting

Add a third term to the blend formula:

```
score = 0.60·cosine + 0.25·recency + 0.15·credibility(source)
```

Credibility values (static dict, easily extensible when new sources are added):

| Source | Credibility score |
|--------|-----------------|
| `ft.com` | 1.00 |
| `marketwatch.com` | 0.85 |
| any other (default) | 0.70 |

Credibility is a readiness mechanism: with only FT + MarketWatch the delta is small, but the framework is in place for when lower-quality sources are added in v0.2c.

---

## Implementation

### Files changed

| File | Change |
|------|--------|
| `src/marketpulse/retrieval/retriever.py` | Add constants, `credibility_score()`, `mmr_rerank()`, update `_blend()` and `search()` |
| `tests/test_retriever.py` | Add tests for `credibility_score()`, `mmr_rerank()`, updated blend formula |

### New constants

```python
MMR_LAMBDA = 0.7
N_CANDIDATES_MULTIPLIER = 4   # fetch k * 4 candidates, min 20
CREDIBILITY_WEIGHT = 0.15
SIM_WEIGHT = 0.60             # was 0.70
RECENCY_WEIGHT = 0.25         # was 0.30

SOURCE_CREDIBILITY: dict[str, float] = {
    "ft.com": 1.00,
    "marketwatch.com": 0.85,
}
DEFAULT_CREDIBILITY = 0.70
```

### New functions

```python
def credibility_score(source: str) -> float:
    """Look up source domain in SOURCE_CREDIBILITY, fall back to DEFAULT_CREDIBILITY."""

def mmr_rerank(
    chunks: list[RetrievedChunk],
    embeddings: list[list[float]],
    k: int,
    lam: float = MMR_LAMBDA,
) -> list[RetrievedChunk]:
    """
    Greedy MMR selection.
    chunks and embeddings are parallel lists (same order, same length).
    Returns k chunks maximising relevance-diversity tradeoff.
    """
```

### Updated `_blend()`

```python
def _blend(similarity: float, recency: float, credibility: float) -> float:
    return SIM_WEIGHT * similarity + RECENCY_WEIGHT * recency + CREDIBILITY_WEIGHT * credibility
```

### Updated `search()`

```python
def search(query: str, k: int = DEFAULT_K) -> list[RetrievedChunk]:
    n_candidates = max(k * N_CANDIDATES_MULTIPLIER, 20)
    results = get_collection().query(
        query_embeddings=q_emb_list,
        n_results=n_candidates,
        include=["embeddings", "documents", "metadatas", "distances"],
    )
    # build RetrievedChunk list with credibility in the score
    # call mmr_rerank() to select final k
```

### `RetrievedChunk` dataclass

Add `credibility: float` field alongside existing `similarity` and `recency`.

---

## Public API

`search(query: str, k: int = DEFAULT_K) -> list[RetrievedChunk]` — **signature unchanged**. Callers in `synthesis/answer.py` and `ui/app.py` need no changes.

---

## Testing

All tests are pure Python — no network, no ChromaDB, no LLM.

| Test | What it checks |
|------|---------------|
| `test_credibility_score_known_source` | FT returns 1.0, MarketWatch returns 0.85 |
| `test_credibility_score_unknown_source` | Falls back to DEFAULT_CREDIBILITY |
| `test_blend_includes_credibility` | Updated 3-weight formula is correct |
| `test_mmr_rerank_selects_diverse_chunks` | Given two near-identical chunks, MMR picks the less similar one second |
| `test_mmr_rerank_fewer_than_k` | Returns all chunks when pool < k |
| `test_mmr_rerank_exact_k` | Returns all when pool == k |
| `test_search_returns_k_results` | Integration-style with mocked ChromaDB |

---

## Out of scope

- UI controls for λ or credibility weights
- Making credibility configurable at runtime
- New data sources
- Kafka, Postgres, or any infra change
