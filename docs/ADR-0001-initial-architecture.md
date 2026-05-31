# ADR-0001: Initial RAG Stack Architecture

**Date:** 2026-05-28
**Status:** Accepted

## Context

MarketPulseAI needed a working RAG pipeline over financial news for a v0.1 demo. Key constraints: free-tier LLM only, local-first (no cloud infra required), beginner-friendly setup, fast iteration.

## Decision

Selected the following stack:

| Component | Choice | Reason |
|-----------|--------|--------|
| **Vector store** | ChromaDB (local `PersistentClient`) | Zero infra, runs on disk, Python-native |
| **Distance metric** | Cosine (not default L2) | Better for normalized sentence embeddings |
| **Embedder** | `BAAI/bge-small-en-v1.5` (local) | 33MB, 384 dims, no API cost, good English quality |
| **LLM** | Gemini Flash (`gemini-flash-latest`) | 1500 req/day free tier, modern `google-genai` SDK |
| **UI** | Streamlit | Zero frontend complexity for a demo |
| **RSS sources** | FT + MarketWatch | Public feeds, no auth required |

## Consequences

**Enables:**
- End-to-end pipeline with `make ingest && make ui` — no cloud setup
- Free operation within Gemini's 1500 req/day limit
- Provider swap is a one-line change via `LLMProvider` Protocol

**Rules out (until explicitly revised):**
- Horizontal scaling (ChromaDB is not distributed)
- Offline/air-gapped LLM (Gemini requires internet)
- Sub-100ms retrieval at scale (local ChromaDB has limits)

## Related ADRs

None yet.
