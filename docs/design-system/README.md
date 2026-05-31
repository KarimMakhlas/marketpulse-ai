# MarketPulse AI — Design System

> Real-time Financial Intelligence Platform · LLMOps-grade RAG over live market data

MarketPulse AI is a **production-grade LLMOps platform** for asking financial questions and getting answers backed by real-time market intelligence. It is **not a chatbot.** Every answer ships with its retrieval trace, source credibility, hallucination risk, RAGAS evaluation scores, and a per-agent latency/cost breakdown — so analysts, quants, and risk teams can verify before they trust.

The platform's visual identity is the **Bloomberg Terminal** crossed with **ChatGPT** and **Datadog**: dense, dark, monospace-leaning data surfaces; a calm conversational query console; and observability dashboards that always reveal *why* an answer looked the way it did.

---

## Surfaces

| # | Surface | Purpose |
|---|---|---|
| 1 | **Dashboard** | Ingestion + quality KPIs at a glance — RAGAS faithfulness, latency, alerts, Kafka health. |
| 2 | **Query Console** | Streaming financial Q&A. Shows live agent progress (Router → Retrieval → Critique → Synthesis → Grader). |
| 3 | **Answer + Citations** | Token-streamed answer with confidence, hallucination flag, latency, trace ID, source cards. |
| 4 | **Retrieval Transparency** | "Why this answer?" — retrieved vs kept vs rejected documents, evidence sufficiency. |
| 5 | **Agent Trace Timeline** | LangGraph/Langfuse-style per-agent timeline with duration, model, tokens, cost. |
| 6 | **Query History** | Tabular log of past queries with confidence and trace links. |
| 7 | **LLMOps Monitoring** | RAGAS faithfulness / answer relevancy / context precision / hallucination rate over time. |
| 8 | **Data Sources** | Ingestion-layer health per source (Reuters, Bloomberg, FT, WSJ, Yahoo, SEC EDGAR, Reddit, X, NewsAPI). Kafka pipeline visualization. |
| 9 | **Admin / Settings** | Retrieval, RAGAS thresholds, source weighting, model selection, rate limits. |

## Backend architecture (for visual reference)

Five-agent LangGraph orchestration with Langfuse tracing:

```
Query → Router → Retrieval → Critique → Synthesis → Grader → Answer
                                ↓
                          (Self-RAG critique loop)
```

Kafka stream: `raw.articles → clean.articles → embedded.articles → ChromaDB`. RAGAS evaluations run on a rolling window; alerts fire when faithfulness < 0.80.

---

## Provided context

The user did **not** attach a codebase, Figma file, or screenshots — this design system was synthesized from the written product brief. If a real implementation exists, please re-attach via the Import menu so we can ground colors, type, and components in reality.

## Index

| Path | What's in it |
|---|---|
| `colors_and_type.css` | All design tokens — color, type, spacing, radius, shadow, motion. Import this everywhere. |
| `fonts/` | Geist Sans + Geist Mono font files (woff2). |
| `assets/` | Logos, source-brand marks, agent glyphs, illustrations. |
| `preview/` | Design System tab cards (palette swatches, type specimens, component states, etc). |
| `ui_kits/web/` | Production-grade UI kit for the MarketPulse web app — JSX components + interactive `index.html`. |
| `SKILL.md` | Manifest for re-use as a Claude Skill. |

See **CONTENT FUNDAMENTALS**, **VISUAL FOUNDATIONS**, and **ICONOGRAPHY** sections below.

---

## CONTENT FUNDAMENTALS

### Voice
**Analyst-grade, never breezy.** MarketPulse copy reads like the chyron of a financial terminal or the header of an internal eval dashboard: factual, compact, observable. Numbers are the heroes; words are scaffolding. If a sentence could appear in a Bloomberg headline *or* a Datadog runbook, it's on-brand.

### Tone rules
- **Address the reader as "you" only in onboarding and empty states.** Everywhere else, use the imperative ("Ask a question", "Inspect trace", "Open source") or the noun-phrase headline ("Faithfulness over time", "Rejected documents").
- **No "we", no "our".** This isn't a personality, it's an instrument.
- **No exclamation points.** Ever. Not even in success states. ("Query streamed in 1.8s" — full stop.)
- **No hedging adverbs.** Cut "just", "simply", "quickly", "easily", "powerful". A faithfulness score of 0.89 is not "impressive" — it's `0.89`.
- **Past tense for completed agent actions.** Present tense (ing-form) for in-flight ones. `Retrieved 12 documents` vs `Generating answer…`.

### Casing
- **Sentence case** for headlines and labels: "Live market intelligence query", not "Live Market Intelligence Query".
- **ALL-CAPS** reserved for: agent labels in trace timelines (`ROUTER`, `SYNTHESIS`), severity pills (`CRITICAL`, `WARN`), and section eyebrows (`SOURCES`, `EVIDENCE`). Always letter-spaced +0.08em.
- **Numbers first, units second**, no space for currency/percent (`$0.0042`, `86%`), one thin space for SI (`1.8 s`, `12 docs`, `2.4 k tok`).

### Vocabulary
| Use | Don't use |
|---|---|
| Query, prompt | Question (in UI; OK in onboarding) |
| Agent | Bot, assistant |
| Trace | Log, history |
| Source | Reference, citation (citation = inline `[S1]` marker only) |
| Credibility | Trustworthiness |
| Faithfulness, relevancy, precision | Accuracy (RAGAS terms are load-bearing) |
| Hallucination risk | Made-up, fake |
| Ingestion | Sync, import |
| Streaming | Loading, fetching |

### Numeric formatting
- Currency: `$0.0042` (4dp for per-query cost), `$12.40` (2dp for daily roll-ups)
- Latency: `1.8 s` (1dp under 10s), `230 ms` (no decimals under 1s)
- Tokens: `2.4k`, `1.2M` (k/M abbreviation, no space)
- Confidence/RAGAS scores: `0.86`, `0.89` (2dp, no leading space, no percent)
- Hallucination rate: `7.4%` (1dp, percent symbol attached)
- Counts: `52,430` (thousands separators)
- Dates: `2026-04-12` (ISO) for trace tables; `Apr 12, 2026 · 14:32 UTC` for timestamps in cards
- Relative time: `2 min ago`, `4 h ago` (one space, abbreviated unit)

### Empty / loading / error states
- Empty: state the absence as a fact, never an apology. `No queries yet. Submit one above.`
- Loading: name the in-flight action. `Retrieving sources…`, not `Loading…`.
- Error: state the failure + the recovery. `Kafka topic clean.articles stalled. Restart consumer.`
- Hallucination warning: blunt. `Hallucination risk: High. Verify with cited sources.`

### Examples — what good copy looks like
- ✅ `0 alerts in last 24 h`
- ✅ `Retrieved 12. Kept 5 after critique.`
- ✅ `Confidence 0.86 · Hallucination low · 1.8 s · trace tr_8f3a…`
- ✅ `Reddit post rejected — credibility 0.31 below threshold 0.55.`
- ❌ `Great news — we found some sources for you!`
- ❌ `Oops! Something went wrong.`
- ❌ `Powered by our state-of-the-art AI`

### Emoji
**No emoji in product chrome.** The only sanctioned glyphs are status dots (●), check/warn/cross marks rendered as Lucide icons, and currency/math symbols. Emoji in error toasts, dashboard cards, or marketing copy are off-brand.

---

## VISUAL FOUNDATIONS

### Mood
**Instrument, not interface.** The screen is a workbench for a finance professional who already trusts data and wants the platform to surface *more* of it, faster. No celebratory color. No marketing gloss. The product reveals its machinery — agent traces, retrieval rejections, eval scores — because revealing is the trust mechanism.

### Color philosophy
Dark mode is the default and only theme. The palette is calibrated for **long sessions on a 27" external monitor at 80% brightness** — high contrast where it matters (data, alerts), low contrast everywhere else (chrome, dividers, secondary labels).

- **Backgrounds** are a near-black ramp with a faint cool tint (`#07090C → #11151B → #181D26`), never pure `#000` (which would crush OLED glyph anti-aliasing).
- **Foregrounds** are warm off-white (`#E8EAED`) for primary text, stepping down through neutrals to `#5B6473` for tertiary.
- **Accent — Signal Green** (`#00E08F`) marks healthy systems, market gains, and "kept" sources. Bloomberg-amber **Caution** (`#FFB020`) marks degradation. **Loss Red** (`#FF4D6D`) marks market losses, hallucination alerts, and rejected sources.
- **Accent — Violet** (`#7C5CFF`) is reserved for **AI / LLMOps elements only** — agent labels, RAGAS metric titles, model-name pills, trace IDs. This is the load-bearing brand color; using it for anything else dilutes the LLMOps signal.
- **Accent — Sky Blue** (`#4DA3FF`) flags **sources and data ingestion** — source cards, Kafka topics, citation markers.

See `colors_and_type.css` for the full token set.

### Type
- **Geist Sans** for all UI text, labels, headlines, body copy. Modern, technical, calm. Tight default tracking (`-0.01em` on display sizes).
- **Geist Mono** for: numerics in KPI cards, trace IDs, source URLs, agent names in timelines, code, JSON payloads, latency/cost/confidence values.
- **Numeric mode**: enable `font-variant-numeric: tabular-nums` everywhere a number could change in place (KPI cards, streaming token counts, eval scores). Non-negotiable.
- **No serifs.** Financial gravitas comes from numbers and density, not Garamond.

Scale (rem-based, 16px root):

| Token | Size | Use |
|---|---|---|
| `--text-display` | 40 / 44 px | Hero page titles (rare) |
| `--text-h1` | 28 / 34 px | Section title on Dashboard |
| `--text-h2` | 20 / 28 px | Card title |
| `--text-h3` | 16 / 22 px | Sub-card / panel title |
| `--text-body` | 14 / 22 px | Default body |
| `--text-sm` | 13 / 20 px | Secondary body, dense tables |
| `--text-xs` | 12 / 16 px | Labels, captions, eyebrows |
| `--text-mono-data` | 14 / 20 px | KPI numerics |
| `--text-mono-display` | 32 / 36 px | Big KPI number (e.g. `0.89` faithfulness) |

### Spacing
4px base grid. Tokens: `--space-1` (4) · `2` (8) · `3` (12) · `4` (16) · `5` (24) · `6` (32) · `7` (48) · `8` (64). Card internal padding defaults to `--space-5` (24px); compact data tables drop to `--space-2` (8px) vertical padding per row.

### Backgrounds
- **No imagery, no gradients on chrome.** The entire app is flat color fills on the background ramp.
- The single **brand gradient** (`linear-gradient(135deg, #7C5CFF 0%, #4DA3FF 100%)`) appears only on: the wordmark stroke, the AI-agent badge ring, and the active agent's progress bar in the trace timeline.
- A subtle **scanline texture** (1px horizontal lines at 3% white opacity) is optional on hero areas only — homage to the Bloomberg/CRT lineage. Off by default; opt in per surface.

### Borders & dividers
- Default border `1px solid var(--border-subtle)` (`#1C2230`) — barely visible, just enough to separate cards from background.
- Strong border `1px solid var(--border-default)` (`#2A3142`) for focused or selected states.
- **Inset rule** for table row separators: `1px solid rgba(255,255,255,0.04)` — never a full opaque divider.

### Corner radii
**Sharp by default.** Most surfaces use `--radius-1` (4px). Cards use `--radius-2` (6px). Pills and avatars use `--radius-full`. **No oversized rounded-2xl card aesthetic** — that's chatbot territory, and this isn't a chatbot.

| Token | px | Use |
|---|---|---|
| `--radius-0` | 0 | Inline data tables, terminal-style panes |
| `--radius-1` | 4 | Buttons, inputs, badges, most surfaces |
| `--radius-2` | 6 | Cards, modals |
| `--radius-3` | 10 | Large feature surfaces (rare) |
| `--radius-full` | 999 | Pills, avatars, status dots |

### Shadows / elevation
Shadows are **almost invisible** in dark mode — elevation is communicated by `background-color` stepping up the bg ramp, not by drop shadow.

- `--shadow-1`: `0 1px 0 0 rgba(255,255,255,0.04) inset` — top inner highlight for raised cards.
- `--shadow-2`: `0 8px 24px -8px rgba(0,0,0,0.4), 0 1px 0 0 rgba(255,255,255,0.04) inset` — for popovers, dropdowns, command palette.
- `--shadow-glow-ai`: `0 0 0 1px rgba(124,92,255,0.4), 0 0 24px -4px rgba(124,92,255,0.25)` — only on the active agent card during streaming.

### Cards
- Background `--bg-card` (`#11151B`)
- 1px subtle border + `--shadow-1` inner highlight
- 24px internal padding (16px in compact data dense modes)
- 6px radius
- No drop shadow on resting cards. Hover lifts by stepping background to `--bg-card-hover` (`#161B24`), never by shadow.

### Transparency & blur
- **Backdrop blur** only on: modals (`backdrop-filter: blur(12px)` over a `rgba(7,9,12,0.7)` scrim), and the floating command palette.
- **Glass surfaces** are off-brand on the main canvas — they suggest consumer apps, not instruments. Solid fills everywhere else.
- The fixed app header has a `rgba(7,9,12,0.9)` solid (no blur) to keep numerics underneath crisp.

### Motion
**Restraint.** This is an LLMOps platform; jiggling cards distract from data.

- All transitions: `150ms cubic-bezier(0.2, 0, 0, 1)` (snap-out ease). Hover color shifts, focus rings, pill changes all use this single curve.
- **Streaming UI** gets a dedicated treatment: the token cursor (▍) blinks at 1.06s (slightly slower than CSS default to match GPT's cadence). Active agent's progress bar uses a 1.8s indeterminate sweep.
- **No bounces, no parallax, no card hover-rotates.** The trace timeline connector dot pulses (1px scale, 1.4s loop) only while its agent is in-flight.
- Number changes (KPI tickers) use a 240ms cross-fade only — never a slot-machine roll.
- Page transitions: instant. The app should feel like a terminal, not an SPA.

### Hover states
- **Buttons**: background lightens by ~6% (mix-with-white 6%), border stays. Never opacity-fade.
- **Links / source cards**: foreground brightens to `--fg-primary`, optional 1px underline on text links only.
- **Table rows**: background steps to `--bg-row-hover` (`#161B24`). Cursor → pointer only if the row is clickable (most are).
- **No transform on hover** for chrome elements — too jittery during dense scanning.

### Press / active states
- Buttons darken by ~6% and shrink `scale(0.98)` for 80ms then settle. The shrink is the only intentional micro-bounce in the system.
- Toggles, switches: instant color swap, no animation overshoot.

### Focus rings
2px ring offset 1px, `var(--accent-ai)` for AI surfaces, `var(--accent-info)` for data surfaces, `var(--fg-primary)` neutral for chrome. Never use the system default blue.

### Layout
- 1440px max-width main canvas, centered, with a fixed 240px **left rail** (nav) and an optional 360px **right rail** (trace inspector, source panel).
- Fixed top header, 56px tall, app-wide. Contains: wordmark, environment pill (`PROD` / `STAGING`), command-palette input (cmd+K), user menu, alert bell.
- Density is **dense but readable**: 22px line-height on body, 14px default body size, but generous `--space-5` (24px) gutters between cards.
- Tables can go to 8px row padding for power-user density screens (Query History, Data Sources).

### Imagery
- **No photography** in the product. Imagery is reserved for marketing surfaces (out of scope here).
- **Source logos** are flat single-color SVG marks rendered at `--fg-primary` opacity 0.7 in source cards. Color logos are off-brand inside the app — they would compete with the data palette.

---

## ICONOGRAPHY

### System
**Lucide Icons** (loaded from CDN — `https://unpkg.com/lucide@latest`). Lucide's stroke-based vector style — 1.5px stroke, 24×24 grid, rounded line joins — pairs cleanly with Geist's geometry and reads well at small sizes in dense panels.

Default render: `stroke-width: 1.5`, `color: currentColor`, 16×16 inline with text, 20×20 in nav rails, 14×14 inside compact pills. Larger sizes (28–32) are reserved for empty-state illustrations.

### Custom / domain icons
A small set of **product-specific glyphs** lives in `assets/icons/`:
- `agent-router.svg`, `agent-retrieval.svg`, `agent-critique.svg`, `agent-synthesis.svg`, `agent-grader.svg` — one geometric glyph per agent, used in trace timelines and progress steppers.
- `source-reuters.svg`, `source-bloomberg.svg`, etc. — monogram-style single-color source marks for source cards.
- `wordmark.svg`, `mark.svg` — MarketPulse wordmark and standalone mark.

These are flat single-color SVGs designed to inherit `currentColor` so they tint with semantic state (kept = green, rejected = red, in-flight = violet).

### Status dots & glyphs
- `●` (U+25CF) for status indicators — colored per state (green/amber/red/violet). 8×8 with 1px ring of the dot's own color at 30% opacity for a subtle glow.
- `▍` (U+258D) thick-bar half-width — the streaming token cursor.
- `↑` `↓` (U+2191/U+2193) — market direction in pills. Never use emoji 🔼 🔽.

### Emoji
**Forbidden** in product chrome. The only exception is user-generated content rendered from upstream sources (e.g. a Reddit post excerpt may contain emoji — render verbatim, no scrub).

### Substitutions
No real codebase or icon set was provided. **Lucide is a substitution** — please confirm or replace with your actual icon library if one exists.
