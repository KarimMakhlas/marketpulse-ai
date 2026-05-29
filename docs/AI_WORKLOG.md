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

## 2026-05-30 — Merge backend with the design system (live web UI)

**What changed:** Vendored the "MarketPulse AI Design System" web kit into `src/marketpulse/web/` and wired its Query Console to the real backend. FastAPI now serves the UI at `/app` (same-origin, so the WebSocket needs no CORS gymnastics) and redirects `/` → `/app/`. Replaced the kit's canned NVIDIA streaming theatre with the live `WS /query/stream` protocol via a new `api.js` client: real JWT login/register, real `meta`/`token`/`done`/`error` frames, real citations, real `doc_grade`, real refusal handling, and a client-measured round-trip latency. Added `excerpt` to `CitationOut` so source cards show real text. Fabricated metrics from the prototype (per-agent cost, trace id, fake `0.86` confidence, token counts) were replaced with real signals or an honest `—`. Dashboard/Monitoring/Sources/Settings remain static design fixtures — the API exposes no data for them yet.
**Files touched:** `src/marketpulse/web/*` (vendored kit + new `api.js`, rewired `QueryConsole.jsx`, tolerant `SourceCard` in `components.jsx`, fixed CSS path in `index.html`), `src/marketpulse/api/app.py` (StaticFiles mount + root redirect), `src/marketpulse/api/schemas.py` (`CitationOut.excerpt`), `tests/test_api.py` (mount/redirect/excerpt tests), `docs/AI_WORKLOG.md`, `CLAUDE.md`.
**Decisions made:** Kept the kit's no-build React+Babel-CDN approach (beginner-friendly, no node toolchain) and served it from FastAPI rather than standing up a separate Vite app — smallest slice that "merges backend with design." Did NOT touch backend auth: streaming still requires a logged-in user, so the full live answer path needs Postgres (`make stack-up`) + an ingested index + `GEMINI_API_KEY`; without Postgres the login modal surfaces the real 503 ("user store unavailable"). Honesty over fidelity: removed prototype metrics the API can't back rather than display fake numbers (matches the design system's own "numbers are heroes, never fake" rule and the repo's no-aspirational-docs rule).

---

## 2026-05-29 — v0.4 API layer: FastAPI + JWT auth + rate limiting + Docker + CI

**What changed:** Built the full v0.4 deployment/hardening layer. New `src/marketpulse/api/` package: `security.py` (bcrypt hashing + PyJWT issue/verify), `schemas.py` (pydantic models), `deps.py` (DI for provider/current-user + slowapi limiter), `app.py` (factory with `GET /health`, `POST /auth/register`, `POST /auth/token`, protected `POST /query`, and `WS /query/stream`), `__main__.py` (uvicorn entry, `make api`). Extended `db/client.py` with a `users` table + `create_user`/`get_user`/`db_available` and two auth exceptions (auth raises instead of no-op'ing like audit writes). Added Alembic (`migrations/` + `0001_initial_schema`), a uv-based `Dockerfile`, a root `docker-compose.yml` full stack (API + Postgres + Redis + Kafka), and GitHub Actions CI (ruff + format + mypy --strict + pytest + offline alembic). 20 new tests (`test_security.py`, `test_api.py`) → 105 total. Verified live: `make api` serves /health 200, /docs, and 401 on unauthenticated /query.
**Files touched:** `src/marketpulse/api/*` (new), `src/marketpulse/db/client.py`, `src/marketpulse/db/__init__.py`, `tests/test_security.py` + `tests/test_api.py` (new), `alembic.ini`, `migrations/*` (new), `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `.github/workflows/ci.yml`, `Makefile`, `.env.example`, `pyproject.toml`, `src/marketpulse/__init__.py` (0.4.0), `CLAUDE.md`, `docs/MVP_SCOPE.md`
**Decisions made:** All LLM access in the API goes through the injected `LLMProvider` (tests override via `app.dependency_overrides`; WebSocket calls `get_provider()` directly). WebSocket auth via `?token=` query param (browsers can't set WS headers). Rate-limit test uses an isolated `Limiter`, not the module singleton, because slowapi's in-process window is shared and keyed by client IP. MemorySaver kept for the LangGraph checkpointer (no PostgresSaver) — single-instance scope. Hetzner/Cloudflare deploy intentionally left as a documented user-run step (needs their accounts), not executed from here. Hit a FastAPI gotcha: with `from __future__ import annotations`, route param types must be importable at module level or FastAPI returns 422 — logged in CLAUDE.md.

---

## 2026-05-29 — Fix Streamlit deprecation box + Langfuse warning spam

**What changed:** Hunted bugs across the interface and backend. Three real fixes: (1) `use_container_width=True` on the Ask button is deprecated in Streamlit 1.57 and renders an inline yellow deprecation box in the app — replaced with `width="stretch"`. (2) Langfuse was *not* the "transparent no-op" the docs claimed: with langfuse 4.7 installed, `from langfuse import observe` returns the real decorator, which logs `Authentication error... Client will be disabled` on every grade + answer call (twice per query) when no keys are set. Centralised the decorator resolution in a new `observability.py` shim that only uses the real `@observe` when `LANGFUSE_PUBLIC_KEY`+`LANGFUSE_SECRET_KEY` are present, else a genuine typed no-op. (3) `ensure_schema()` ran on every Streamlit rerun (reconnecting to Postgres + re-warning each keystroke) — wrapped in `@st.cache_resource` so it runs once per process. Verified the full `answer()` pipeline end-to-end against the real index with a fake provider (5 citations, grading, streaming all correct) and confirmed the app boots HTTP 200 with a clean log.
**Files touched:** `src/marketpulse/observability.py` (new), `src/marketpulse/synthesis/answer.py`, `src/marketpulse/graph/nodes.py`, `src/marketpulse/ui/app.py`, `docs/AI_WORKLOG.md`
**Decisions made:** Typed the shared `observe` as an identity-decorator Protocol so `mypy --strict`'s disallow_untyped_decorators stays happy (a raw runtime-resolved value erases the decorated fn to `Any`). Did not change the two-Gemini-calls-per-query design (grade + answer) — the grading call is the core Self-RAG feature; flagged separately that it doubles free-tier quota consumption (~10 questions/day against the 20 req/day limit).

---

## 2026-05-29 — v0.3 Self-RAG LangGraph pipeline + Langfuse + RAGAS eval

**What changed:** Replaced direct retrieve→generate flow with a LangGraph StateGraph (retrieve → grade_docs → route → build_prompt|refuse). grade_docs uses a new synchronous `provider.generate()` method to ask the LLM if retrieved docs are relevant; insufficient sources trigger a refusal branch instead of hallucinating. Langfuse `@observe()` decorates grader nodes (transparent no-op without credentials). Added `alerts` and updated `query_log` (now stores doc_grade) Postgres tables. Added RAGAS eval script at `scripts/evaluate.py` (`make eval`). Fixed a silent credibility score bug: INSUFFICIENT was matching as SUFFICIENT due to substring check.
**Files touched:** `src/marketpulse/graph/` (new), `src/marketpulse/llm/provider.py`, `src/marketpulse/llm/gemini.py`, `src/marketpulse/synthesis/answer.py`, `src/marketpulse/synthesis/prompts.py`, `src/marketpulse/db/client.py`, `src/marketpulse/db/__init__.py`, `src/marketpulse/ui/app.py`, `tests/test_graph.py`, `tests/test_answer.py`, `Makefile`, `scripts/evaluate.py`, `.env.example`, `pyproject.toml`, `uv.lock`
**Decisions made:** Streaming UX preserved by running the graph sync (grading only) then streaming outside the graph. MemorySaver chosen over PostgresSaver to avoid psycopg3 dep — sufficient for single-user local demo. RAGAS eval uses no ground truth (online eval only).

---

## 2026-05-29 — v0.2 additional scrapers (Yahoo, CNBC, Guardian, SEC EDGAR, NewsAPI)

**What changed:** Expanded ingestion from 2 to 7 sources. Added Yahoo Finance, CNBC, Guardian Business as free RSS feeds. Added SEC EDGAR 8-K/10-Q via the EFTS JSON API (httpx, no auth required). Added optional NewsAPI source (graceful no-op if NEWS_API_KEY unset). Fixed SOURCE_CREDIBILITY keys in retriever (were "ft.com"/"marketwatch.com", must match the source metadata key "ft"/"marketwatch"). Total ingestion now yields ~163 articles per run.
**Files touched:** `src/marketpulse/ingestion/sources.py`, `src/marketpulse/ingestion/indexer.py`, `src/marketpulse/retrieval/retriever.py`, `tests/test_sources.py`, `tests/test_retriever.py`, `pyproject.toml`, `uv.lock`
**Decisions made:** SEC EDGAR Atom feed URLs were malformed (feedparser bozo=mismatched tag) — replaced with EFTS JSON API. Source credibility key bug was a silent regression: all sources were falling back to DEFAULT_CREDIBILITY (0.70) because the dict used domain names instead of source keys.

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
