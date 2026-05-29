# AI Worklog

Running log of AI-assisted work sessions. Newest entries at the top.

Format:
```
## YYYY-MM-DD — <topic>

**What changed:** <1-2 sentences>
**Files touched:** <comma-separated list>
**Decisions made:** <any non-obvious choices, or "none">
```

---

## 2026-05-29 — v0.2 Postgres integration (articles + query_log)

**What changed:** Added `src/marketpulse/db/` module with psycopg2-backed `articles` and `query_log` tables. Ingestion writes article metadata to Postgres after each Chroma upsert; synthesis logs each query + chunk URLs before streaming. If `DATABASE_URL` is unset or Postgres is unreachable, all DB calls are silent no-ops so existing `make ingest` / `make ui` flows are unaffected.
**Files touched:** `src/marketpulse/db/client.py`, `src/marketpulse/db/__init__.py`, `src/marketpulse/ingestion/indexer.py`, `src/marketpulse/ingestion/__main__.py`, `src/marketpulse/synthesis/answer.py`, `.env.example`, `tests/test_db.py`
**Decisions made:** Graceful degradation (no-op when DB unavailable) keeps the tool usable without Postgres. Answer text not logged — requires buffering the stream, deferred. `asyncio.to_thread` not yet wired into Kafka consumer (consumer calls indexer which calls upsert_article synchronously — acceptable for now since consumer is the only async caller and the upsert is fast).

---

## 2026-05-28 — v0.2 Kafka streaming ingestion pipeline

**What changed:** Added async Kafka producer (5-min RSS polling) and consumer (embed + ChromaDB upsert). `make ingest` still works one-shot. `make kafka-up && make producer` / `make consumer` runs the streaming pipeline. Docker Compose runs bitnami/kafka in KRaft mode (no Zookeeper).
**Files touched:** `src/marketpulse/ingestion/producer.py`, `consumer.py`, `pipeline.py`, `__main__.py`, `docker/docker-compose.yml`, `Makefile`, `tests/test_pipeline.py`
**Decisions made:** Producer deduplicates against ChromaDB on startup (seen-set). Consumer is idempotent via upsert. KRaft mode chosen (no Zookeeper needed for single-node local dev).

---

## 2026-05-28 — v0.2 retrieval: MMR re-ranking + source credibility

**What changed:** Replaced naive top-k sort with MMR re-ranking (λ=0.7) over a 4× candidate pool; added source credibility as a third blend weight (0.60·cosine + 0.25·recency + 0.15·credibility). Public `search()` API unchanged.
**Files touched:** `src/marketpulse/retrieval/retriever.py`, `tests/test_retriever.py`, `tests/test_answer.py`, `tests/test_prompts.py`
**Decisions made:** Credibility dict is static for now (FT=1.0, MarketWatch=0.85, default=0.70) — framework is in place for when lower-quality sources are added. MMR uses raw embeddings from ChromaDB (requires `include=["embeddings"]` in query).

---

## 2026-05-28 — Claude Code workspace scaffold

**What changed:** Created the full `.claude/` workspace structure — 8 subagents, 6 skills, rules, hooks, docs stubs, and utility scripts.
**Files touched:** `.claude/agents/*.md`, `.claude/skills/*/SKILL.md`, `.claude/rules/*.md`, `.claude/hooks/*.sh`, `docs/PRODUCT_BRIEF.md`, `docs/TESTING_STRATEGY.md`, `docs/DECISIONS/ADR-0001-initial-architecture.md`, `scripts/*.sh`, `CLAUDE.local.md`
**Decisions made:** Rules and hooks in `.claude/` are gitignored along with the rest of `.claude/` — kept local-only per existing `.gitignore` convention.
