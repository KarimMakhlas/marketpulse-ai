# Product Brief: MarketPulseAI

## Problem

Financial professionals and retail investors spend hours manually tracking news across multiple sources. Relevant market-moving information is fragmented, delayed, and hard to query in natural language.

## Target Users

- Retail investors wanting quick context on market events
- Financial analysts needing fast synthesis across sources
- Developers learning to build RAG pipelines on financial data

## Key Features (v0.1 — complete)

| Feature | Status |
|---------|--------|
| RSS ingestion (FT + MarketWatch) | Done |
| Content-hash dedup | Done |
| Local embedding (bge-small-en-v1.5) | Done |
| ChromaDB vector store (cosine) | Done |
| Recency-weighted retrieval | Done |
| Cited answer synthesis via Gemini | Done |
| Streamlit UI | Done |

## Deferred Features (v0.2+)

See `docs/MVP_SCOPE.md` for the full roadmap. Key items deferred: additional news sources, multi-agent reasoning, evaluation framework, production deployment.

## Success Metrics (v0.1)

- End-to-end pipeline runs locally with `make ingest && make ui`
- Answers cite specific articles with publication dates
- Retrieval latency < 500ms (excluding LLM)
- All 34 unit tests pass in < 2s
