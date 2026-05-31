# MarketPulse AI

> End-to-end Self-RAG system over financial news. Ingests 7+ live sources, runs a
> LangGraph grader/router pipeline, and streams cited answers through a FastAPI +
> React web UI.

**Status: v0.4 — complete.** All milestones shipped (v0.1 → v0.4). See
[`docs/AI_WORKLOG.md`](docs/AI_WORKLOG.md) for the per-version history and
[`docs/MVP_SCOPE.md`](docs/MVP_SCOPE.md) for the deferral table.

![MarketPulse AI — query, streamed answer with inline citations, and ranked sources](docs/screenshot.png)

---

## What it does

```
USER:  "What did the financial press report about the Fed this week?"

  │ make ingest         7 sources → dedup → chunk → BGE-small embed
  │ (or make kafka-up   → producer polls every 5 min → Kafka → consumer)
  │
  │ LangGraph pipeline  retrieve → grade_docs → route
  │                     → build_prompt  ← enough graded sources
  │                     → refuse        ← insufficient sources
  │
  │ GeminiProvider      stream cited answer via WS /query/stream
  │
  ▼ make api            React web UI at http://localhost:8000/app
                        (streamed answer + citations + live dashboard)
```

Sources: FT · MarketWatch · Yahoo Finance · CNBC · The Guardian · SEC EDGAR
(8-K + 10-Q) · NewsAPI (optional). Retrieval re-ranks with MMR (λ=0.7) and
blends `0.60·cosine + 0.25·recency + 0.15·credibility`.

---

## Quickstart

```bash
# Prereqs: Python 3.12+, uv (https://docs.astral.sh/uv/),
#          a free Gemini API key (https://aistudio.google.com/apikey)

git clone <this-repo>
cd MarketPulseAI

# 1. Install deps (first run downloads PyTorch + sentence-transformers, ~1 GB)
uv sync

# 2. Add your Gemini key
cp .env.example .env
# edit .env and paste GEMINI_API_KEY=...

# 3. Pull articles and index them
make ingest          # ~10–30 s, idempotent

# 4. Ask a question via CLI (no server needed)
make ask Q="What is the financial press saying about AI chip stocks?"

# 5. Or launch the full API + web UI
make api             # → open http://localhost:8000/app
```

Register a user, log in, and query from the browser. The API docs are at
`http://localhost:8000/docs`.

---

## Commands

| Command | What it does |
|---|---|
| `make ingest` | One-shot ingestion of all 7 sources → embed → upsert |
| `make kafka-up` / `make producer` / `make consumer` | Streaming ingestion via Kafka (requires Docker) |
| `make query Q="…"` | Retrieval only — no LLM call, useful for tuning |
| `make ask Q="…"` | Full Self-RAG via CLI (requires `GEMINI_API_KEY`) |
| `make api` | FastAPI at http://localhost:8000 — serves the React UI at `/app` |
| `make eval` | RAGAS evaluation over a hardcoded question set (uses Gemini quota) |
| `make migrate` | `alembic upgrade head` against `DATABASE_URL` |
| `make stack-up` / `make stack-down` | Full Docker stack: API + Postgres + Redis + Kafka |
| `make lint` / `make fmt` | ruff |
| `make typecheck` | mypy strict on `src/marketpulse/` |
| `make test` | pytest, 120 unit tests, ~5 s (no network, no LLM, no real DB) |

---

## Project structure

```
frontend/src/          React web UI (Babel-CDN, no build step)
                       api.js drives live WS + read endpoints;
                       every screen wired to the API (live values or
                       honest "—"/"Not wired", never fabricated data).
                       Served by FastAPI at /app.

src/marketpulse/
  ingestion/           sources.py + indexer.py
                       + kafka_config.py / producer.py / consumer.py
  retrieval/           retriever.py — MMR + credibility blend
  graph/               state.py + nodes.py + build.py — LangGraph Self-RAG
  llm/                 provider.py (Protocol) + gemini.py
  synthesis/           answer.py — prompt orchestration + streaming
  db.py                Postgres store: users + query_log + alerts
  observability.py     Langfuse @observe shim (no-op without creds)
  api/                 security.py + schemas.py + deps.py + app.py
                       POST /query · WS /query/stream · GET /health
                       GET /stats · GET /sources · GET /queries

tests/                 120 unit tests — strict isolation
scripts/               evaluate.py (RAGAS eval)
migrations/            Alembic env + versions/
docs/                  AI_WORKLOG, MVP_SCOPE, PRODUCT_BRIEF,
                       TESTING_STRATEGY, design-system/
docker/                docker-compose.kafka.yml
docker-compose.yml     Full stack (API + Postgres + Redis + Kafka)
Dockerfile             API image (uv-based)
.github/workflows/     CI: lint + format + mypy + pytest + alembic check
```

---

## Tech stack

`uv` · `ruff` · `mypy --strict` · `pytest-cov` · `feedparser` · `httpx` ·
`sentence-transformers` (BGE-small-en-v1.5, local) · `chromadb`
(PersistentClient, cosine) · `langgraph` · `google-genai` (`gemini-flash-latest`)
· `fastapi` + `uvicorn` · `python-jose` + `bcrypt` (JWT/OAuth2) · `slowapi`
(rate limiting) · `psycopg2` · `alembic` · `kafka-python` · `langfuse` ·
`ragas` · `python-dotenv`

---

## Design highlights

- **Self-RAG via LangGraph** — `grade_docs` scores each retrieved chunk against
  the query; the router branches to `build_prompt` when enough chunks pass, or
  `refuse` when they don't. No hallucinated answers when sources are thin.
- **Provider abstraction** (`src/marketpulse/llm/provider.py`) — `LLMProvider`
  is a `typing.Protocol`. Swapping Gemini for any other model is one new file.
- **Streaming over WebSocket** — `WS /query/stream` pushes `meta` / `token` /
  `done` / `error` frames so the UI renders the answer word-by-word.
- **Idempotent ingestion** — chunks are keyed by `sha256(url)_chunk_idx`, so
  re-running `make ingest` upserts without accumulating duplicates.
- **Cosine + normalized embeddings** — Chroma's default distance is L2; the
  collection is explicitly created with `hnsw:space=cosine` and BGE embeddings
  are L2-normalized at both index and query time.
- **Honest UI** — every dashboard metric comes from a real API endpoint or
  renders as `—`. No fabricated numbers, no `Math.random()` charts.
- **Graceful degradation** — Postgres, Redis, Kafka, Langfuse, and NewsAPI are
  all optional. The core `make ingest` + `make ask` flow works with just a
  Gemini key.
