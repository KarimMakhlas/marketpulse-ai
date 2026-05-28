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

## 2026-05-28 — Claude Code workspace scaffold

**What changed:** Created the full `.claude/` workspace structure — 8 subagents, 6 skills, rules, hooks, docs stubs, and utility scripts.
**Files touched:** `.claude/agents/*.md`, `.claude/skills/*/SKILL.md`, `.claude/rules/*.md`, `.claude/hooks/*.sh`, `docs/PRODUCT_BRIEF.md`, `docs/TESTING_STRATEGY.md`, `docs/DECISIONS/ADR-0001-initial-architecture.md`, `scripts/*.sh`, `CLAUDE.local.md`
**Decisions made:** Rules and hooks in `.claude/` are gitignored along with the rest of `.claude/` — kept local-only per existing `.gitignore` convention.
