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

## 2026-05-28 — v0.2 retrieval: MMR re-ranking + source credibility

**What changed:** Replaced naive top-k sort with MMR re-ranking (λ=0.7) over a 4× candidate pool; added source credibility as a third blend weight (0.60·cosine + 0.25·recency + 0.15·credibility). Public `search()` API unchanged.
**Files touched:** `src/marketpulse/retrieval/retriever.py`, `tests/test_retriever.py`, `tests/test_answer.py`, `tests/test_prompts.py`
**Decisions made:** Credibility dict is static for now (FT=1.0, MarketWatch=0.85, default=0.70) — framework is in place for when lower-quality sources are added. MMR uses raw embeddings from ChromaDB (requires `include=["embeddings"]` in query).

---

## 2026-05-28 — Claude Code workspace scaffold

**What changed:** Created the full `.claude/` workspace structure — 8 subagents, 6 skills, rules, hooks, docs stubs, and utility scripts.
**Files touched:** `.claude/agents/*.md`, `.claude/skills/*/SKILL.md`, `.claude/rules/*.md`, `.claude/hooks/*.sh`, `docs/PRODUCT_BRIEF.md`, `docs/TESTING_STRATEGY.md`, `docs/DECISIONS/ADR-0001-initial-architecture.md`, `scripts/*.sh`, `CLAUDE.local.md`
**Decisions made:** Rules and hooks in `.claude/` are gitignored along with the rest of `.claude/` — kept local-only per existing `.gitignore` convention.
