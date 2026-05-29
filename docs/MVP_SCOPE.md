# MarketPulse AI — MVP Scope (v0.1)

> **Contract with myself:** this document defines what "v1 done" means for MarketPulse AI. Anything not listed in **In scope** below is deferred to a later version, even if it appears in `MarketPulseAI-TechSpec.md`. The spec is the long-term architecture; this is the smallest demo-able slice.

---

## Goal

A working financial-news RAG demo: ingest 2 RSS feeds → answer questions about recent finance news with cited sources, runnable locally in under 5 minutes.

---

## In scope

The seven things v0.1 commits to building:

1. **RSS ingestion** — 2 feeds (Financial Times + MarketWatch) via `feedparser`, plain Python script run on demand. No Kafka, no `aiokafka`. Reuters' public RSS was discontinued and is no longer reachable; MarketWatch substituted. The 5-min polling timer is deferred to v0.2 — v0.1 is one-shot only (`make ingest` runs once and exits; re-run manually for fresh data).
2. **Storage** — ChromaDB only, running as an in-process `PersistentClient` (file path `./data/chroma`, no Docker, no separate server). Article metadata (`url`, `source`, `title`, `published_at`, `ingested_at`) lives on chunk metadata in Chroma. Dedup key is content-hash, set as the chunk ID so re-runs upsert cleanly. No Postgres in v0.1 — nothing reads from it yet.
3. **Chunking + embedding** — `RecursiveCharacterTextSplitter` (chunk 800, overlap 120) + `BAAI/bge-small-en-v1.5` running locally via `sentence-transformers`. No paid embedding APIs.
4. **Retriever** — cosine similarity over Chroma + exponential recency decay, top-k=5. No MMR. No source-credibility weighting.
5. **LLM call** — single synthesis call to **Gemini 1.5 Flash** (free tier, 1500 req/day) with inline `[S1] [S2]` citations and an explicit "say so if sources don't answer the question" instruction.
6. **LLM provider abstraction** — a thin `LLMProvider` Python interface (one `generate(prompt) -> str` method) so swapping to Groq or local Ollama is a one-line config change. Avoids hard-coding Gemini SDK calls into application code.
7. **UI** — Streamlit page: text input → answer → list of cited sources with working URLs.

---

## Out of scope (explicitly deferred)

Each item is tagged with the version where it returns. These are **not** missing features — they are deliberately postponed to keep v0.1 shippable in ~2 weekends.

| Deferred to v0.2 | Deferred to v0.3 | Deferred to v0.4 |
|---|---|---|
| Kafka topology + `aiokafka` producers/consumers | Multi-agent LangGraph orchestration | FastAPI app + WebSocket `/query/stream` |
| SEC EDGAR, Reddit PRAW, Twitter, NewsAPI, Yahoo, Bloomberg, WSJ scrapers (10 additional sources) | Self-RAG critique agent + Grader agent | JWT OAuth2 auth + `users` table |
| Source-credibility weighting in retrieval scoring | Refusal branch ("insufficient evidence") | `slowapi` rate limiting backed by Redis |
| MMR re-ranking | Langfuse observability (`@observe` on every node) | Docker Compose full stack |
| Postgres (article table, `query_log` audit table) | RAGAS evaluation cron (every 6h) | Alembic migrations |
| | DeepEval test suite in CI | Hetzner deployment + Cloudflare tunnel |
| | LangGraph `PostgresSaver` checkpointer | GitHub Actions CI pipeline |
| | `alerts` table + Slack webhook on quality drift | |

---

## Done criteria

v0.1 is done when **all four** are true:

1. `make ui` (or equivalent single command) launches the Streamlit app and it loads without error on `http://localhost:8501`.
2. Asking *"What did the financial press report about [a current topic] this week?"* returns a generated answer containing at least 2 inline citation markers (`[S1]`, `[S2]`), and the rendered source list contains at least 2 working URLs that resolve to real articles.
3. Re-running the ingestion script produces **zero duplicate chunks** in ChromaDB (verified by counting collection size before and after a second run on the same feed snapshot).
4. Asking *"What is the airspeed velocity of an unladen swallow?"* (a question with no relevant indexed content) returns either an explicit "the indexed sources don't answer this" response **or** an answer that does not invent a fake citation. No silent hallucination with a fabricated URL.

---

## Milestone status (updated 2026-05-29)

v0.1 is the contract above; v0.2 and v0.3 have since shipped. The original "Out of scope" table is the deferral ladder — this section records which rungs are now done. See `docs/AI_WORKLOG.md` for per-session detail.

### v0.2 — done

1. **Streaming ingestion** — async Kafka producer (5-min RSS polling) + consumer (embed + upsert), Docker Compose Kafka in KRaft mode. One-shot `make ingest` still works.
2. **More sources** — 7 total: FT, MarketWatch, Yahoo, CNBC, Guardian (RSS) + SEC EDGAR (EFTS JSON API) + optional NewsAPI. ~163 articles/run.
3. **MMR re-ranking** — λ=0.7 over a 4× candidate pool.
4. **Source-credibility weighting** — retriever blend is `0.60·cosine + 0.25·recency + 0.15·credibility`.
5. **Postgres audit store** — `articles` + `query_log` tables; no-ops when `DATABASE_URL` unset.

**v0.2 done criteria:** all of the above run without breaking the v0.1 done criteria; `make ingest` remains idempotent; the tool stays fully usable with no Kafka and no Postgres.

### v0.3 — done

1. **LangGraph Self-RAG** — StateGraph: retrieve → grade_docs → route → build_prompt|refuse. Insufficient sources hit a refusal branch.
2. **Doc grading** — synchronous `provider.generate()` asks the LLM whether retrieved docs are relevant; grade stored in `query_log`.
3. **Langfuse observability** — `@observe()` on grader nodes; transparent no-op without credentials.
4. **RAGAS eval** — `scripts/evaluate.py` (`make eval`), online eval, no ground truth.
5. **`alerts` table** — added to the Postgres store.

**v0.3 done criteria:** a no-relevant-content question routes to the refusal branch (no fabricated citation); streaming UX preserved (graph runs sync for grading, streaming happens outside the graph); Langfuse/Postgres absence never breaks the local flow.

> **Quota caveat (overrides Decision #1):** `gemini-flash-latest` now routes to `gemini-3.5-flash` at **20 req/day** on the free tier, not the 1500/day that the older `gemini-1.5-flash` allowed. A single full RAGAS run can exhaust the day's budget — treat `make eval` as roughly one-shot per day.

### v0.4 — done

1. **FastAPI app** (`src/marketpulse/api/`) — `GET /health`, `POST /query` (JSON), `WS /query/stream` (token streaming). All LLM access via the injected `LLMProvider`.
2. **JWT/OAuth2 auth** — `users` table; `POST /auth/register`, `POST /auth/token` (password grant). bcrypt hashing + PyJWT (`api/security.py`). Protected endpoints via `get_current_user`; WebSocket auth via `?token=`.
3. **Rate limiting** — slowapi on the auth + query routes, backed by Redis when `REDIS_URL` is set, in-process memory otherwise.
4. **Alembic migrations** — `migrations/` with `0001_initial_schema` covering articles, query_log, alerts, users. `make migrate`. `ensure_schema()` retained for zero-setup local dev.
5. **Docker** — `Dockerfile` (uv-based API image) + root `docker-compose.yml` full stack (API + Postgres + Redis + Kafka). `make stack-up`.
6. **CI** — `.github/workflows/ci.yml`: ruff check + format check + mypy --strict + pytest + offline Alembic check.

**v0.4 done criteria:** `make api` serves `/health` 200 and Swagger at `/docs`; register→token→`/query` returns a cited answer; `/query` is 401 without a valid token; rate limiting returns 429 past the window; `alembic upgrade head --sql` emits all four tables; the 105-test suite + lint + types are green in CI. All new services degrade gracefully when absent (no Redis → in-memory limiter; no `DATABASE_URL` → auth returns 503, audit no-ops).

### Still deferred (post-v0.4)

**Hetzner + Cloudflare deploy** is scripted/documented but executed by the user (needs their accounts — not run from this repo). Also still open: DeepEval suite, LangGraph `PostgresSaver` (currently `MemorySaver`), Reddit/Twitter scrapers, refresh-token rotation / revocation, per-user quotas.

---

## Time budget

~2 weekends, ~15–20 hours total:

| Slice | Time |
|---|---|
| Python project bootstrap (`uv init`, deps, `Makefile`, ruff config) | 2h |
| RSS ingestion script + dedup-by-content-hash | 3h |
| Chunking + embedding + ChromaDB upsert (in-process `PersistentClient`) | 3h |
| Retriever (cosine + recency) | 2h |
| Gemini integration behind `LLMProvider` interface + synthesis prompt | 3h |
| Streamlit UI | 3h |
| End-to-end wiring, manual testing against done criteria, cleanup | 2h |

If a slice runs significantly over budget, that's a signal to either cut the slice or revisit the scope — not to silently absorb it.

---

## Decision log

| # | Decision | Rationale (one line) |
|---|---|---|
| 1 | **LLM = Gemini 1.5 Flash (free tier)** | Free 1500 req/day, JSON mode works, generous enough for development and demo. Spec assumed paid Mistral — overridden for budget. |
| 2 | **Vector store = ChromaDB local** | Self-hosted, free, no network hop. Same choice as the spec. |
| 3 | **Embeddings = `BAAI/bge-small-en-v1.5` local** | Free, 384 dims, 33MB model. Same choice as the spec. |
| 4 | **UI = Streamlit** | Single Python file, no frontend toolchain. Same choice as the spec. |
| 5 | **No Kafka in v0.1** | Spec assumes Kafka for ~50k events/h. At 2 RSS feeds polled every 5 min (~10 events/min peak) a Python loop is correct sizing; Kafka would be ceremony. Re-introduced in v0.2 once a second worker is justified. |
| 6 | **LLM provider abstracted from day 1** | Cheap to do now (one interface), expensive to retrofit later. Preserves the spec's provider-agnostic property. |
| 7 | **No Postgres in v0.1** | Spec uses Postgres for article metadata, audit log, users, and LangGraph checkpointer. v0.1 has none of those consumers (no users, no audit, no LangGraph). Chroma's chunk metadata is sufficient. Re-introduced in v0.3 when LangGraph + observability land. |
