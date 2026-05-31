---
name: marketpulse-design
description: Use this skill to generate well-branded interfaces and assets for MarketPulse AI, either for production or throwaway prototypes/mocks/etc. Contains essential design guidelines, colors, type, fonts, assets, and UI kit components for prototyping.
user-invocable: true
---

Read the README.md file within this skill, and explore the other available files.

If creating visual artifacts (slides, mocks, throwaway prototypes, etc), copy assets out and create static HTML files for the user to view. If working on production code, you can copy assets and read the rules here to become an expert in designing with this brand.

If the user invokes this skill without any other guidance, ask them what they want to build or design, ask some questions, and act as an expert designer who outputs HTML artifacts _or_ production code, depending on the need.

## Skill contents

- **`README.md`** — Full design system: CONTENT FUNDAMENTALS (voice, tone, casing, numeric formatting), VISUAL FOUNDATIONS (color philosophy, type, spacing, motion, hover/press, layout), ICONOGRAPHY. Read first.
- **`colors_and_type.css`** — All design tokens (CSS custom properties). Import this in every HTML artifact.
- **`fonts/`** — Geist Sans + Geist Mono `.woff2` files. Tied into `colors_and_type.css` via `@font-face`.
- **`assets/`** — Logos (`mark.svg`, `wordmark.svg`), agent glyphs (`icons/agent-*.svg`), source brand marks (`icons/source-*.svg`).
- **`preview/`** — Design System card specimens (palettes, type, components). Useful as visual reference.
- **`ui_kits/web/`** — Working React + JSX UI kit for the MarketPulse web app. Copy components from `components.jsx` and screens (`Dashboard.jsx`, `QueryConsole.jsx`, `Monitoring.jsx`, `DataSources.jsx`, `QueryHistory.jsx`, `Settings.jsx`) when assembling new screens.

## Quick rules

- **Dark mode only.** No light theme.
- **Geist Sans for UI · Geist Mono for numerics, trace IDs, agent labels, code.** Always `tabular-nums` on changing numbers.
- **Sharp by default.** 4 px radius on buttons/inputs, 6 px on cards. No oversized rounded-2xl.
- **Violet (#7C5CFF)** is reserved for AI/LLMOps. **Sky blue (#4DA3FF)** for sources/data. **Signal green / caution amber / loss red** for market and quality signals. Do not reassign.
- **No emoji** in product chrome. No drop shadows on resting cards — elevation by bg-color step.
- **150 ms snap-out** is the only easing curve. Restraint over motion.
- **Sentence case** for headlines. **ALL-CAPS +0.08em** only for eyebrows, agent labels, severity pills.
- **No "we", no exclamation points, no hedging adverbs.** Numbers are the heroes; words are scaffolding.
