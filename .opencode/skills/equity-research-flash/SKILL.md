---
name: equity-research-flash
description: "Produces structured multi-factor price-move attributions, earnings analyses, forensic accounting checks, thesis trackers, sector overviews, and macro-regime reads — a research deliverable, not raw data. Load FIRST, before any data tool or web search, when the user asks: (1) why a single name moved / dropped / rose / sold off / rallied (post-mortem / attribution), (2) what to watch on an upcoming earnings print or how to score the print after it lands, (3) whether accounting quality is suspect (financial forensics / quality-of-earnings), (4) for a thesis, catalyst, scorecard, or watchlist buildout or update on a name, (5) for a sector or theme overview or idea screen, or (6) for a yield-curve or labor-market regime read."
---

# Equity research — workflows dispatcher

Multi-turn institutional equity-research workflows. Each workflow is a
methodology doc that lives under `references/anthropic/` (vendored from
`anthropics/financial-services`, Apache 2.0) or `references/community/`
(vendored from `prof-little-bear/cc-equity-research`, Apache 2.0).

This SKILL.md is the dispatcher. Methodology docs are read on demand —
do NOT preload them.

---

## Data tools — try these BEFORE web search

Most equity-research data needs route to **workspace skills** or
**bundled scripts**, not `firecrawl_search` / `WebFetch`. Quick index
(full mapping + notes in `references/routing.md`):

- US quote / history / fundamentals / news / holders / insiders /
  estimates / per-name calendar / options → `Skill: global-markets`
- CN A-share + HK quote / fundamentals / 板块 / 北向 / 业绩预告 /
  龙虎榜 / 大宗交易 / 解禁 → `Skill: cn-markets`
- Macro (US: NFP / CPI / PCE / curve / OAS via FRED; ECB FX) →
  `Skill: macro-rates-fx`
- Crypto (spot / klines / funding / DeFi TVL) → `Skill: crypto-markets`
- Technical indicators (EMA / RSI / MACD / BBands / ATR / Ichimoku /
  …) → `Skill: ta-engine` (consumes OHLCV from any of the above)
- **SEC filings** (10-K / 10-Q / 8-K / DEF 14A / S-1 / 13F / Form 4 /
  13G/13D + XBRL Frames) → `bash scripts/edgar.py`
- Federal contract awards (defense primes / govtech / public payors)
  → `bash scripts/usaspending.py`

Only fall back to `firecrawl_search` / `WebFetch` for needs not
covered above (broker research notes, conference commentary, deep
qualitative news, third-party blog analysis). See
`references/routing.md` for the full table and the residual gap list
(call-transcript Q&A, curated analyst-grade comp, supplier ontology,
alt-data).

---

## STEP 0 — Confirm scope before doing anything

Before reading any methodology doc, restate to the user:

1. **What category** — discover (idea generation) / analyze (single-name
   deep dive) / monitor (tracked position) / macro (regime read).
2. **What workflow** within the category — e.g. "initiation note",
   "financial forensics", "earnings preview".
3. **What deliverable shape** — e.g. "8-12 page DOCX", "scorecard table
   + 6-pattern verdict", "watchlist update".
4. **Expected turn count** — single-turn (lighter community lenses),
   multi-turn (most Anthropic workflows), or a 5-task pipeline that
   requires explicit per-task user requests (`initiating-coverage`).

Wait for confirmation if the deliverable shape or turn count would
surprise the user. Especially: **never silently start a 5-task
`initiating-coverage` pipeline** in response to "give me a deep dive on
X" — clarify whether they want the full institutional initiation
(5 separately-invoked tasks producing .md + .xlsx + .zip + .docx) or one
of the lighter community lenses (single-turn `business-model`,
`financial-forensics`, etc.).

---

## STEP 1 — Pick the category dispatcher

| Category | Dispatcher | When |
|---|---|---|
| **discover** | `references/discover.md` | User wants ideas, doesn't have a specific ticker, or wants a sector / theme / screen view |
| **analyze** | `references/analyze.md` | User has a specific ticker and wants depth on it |
| **monitor** | `references/monitor.md` | User has tracked names and wants ongoing updates / checks |
| **macro** | `references/macro.md` | User wants a regime read combining multiple macro series |

Read the matching dispatcher. It lists the workflows in that category
and points to the specific methodology doc to follow.

---

## STEP 2 — Read the workflow doc and follow it

The methodology doc tells you what to produce. Treat its instructions
as authoritative for the *shape* of the deliverable, with two overrides
from this skill:

- **Data routing.** Route every data need through
  `references/routing.md`. When the routing table and a methodology
  doc disagree on which tool to call, **the routing table wins**.
- **Output format.** Every deliverable must satisfy
  `references/format.md` — quantification, A/E year notation, citation
  discipline, mandatory `Sources & References` block, institutional tone.

---

## STEP 3 — Disclose data gaps up front

**SEC filings (10-K / 10-Q / 8-K / DEF 14A / S-1 / 13F / Form 4 /
13G/13D) ARE sourced** via `scripts/edgar.py` — use it, don't declare
them a gap. **Federal contract awards** are sourced via
`scripts/usaspending.py`. See `references/routing.md` for the full
matrix before deciding anything is unavailable.

The remaining gap relative to the vendored methodology is
**earnings-call transcripts** (full Q&A with analysts) — used by
`earnings-preview`, `earnings-analysis`, `earnings-scorecard`,
`morning-note`, `thesis-tracker`, `thesis-check`. Press-release
prepared commentary is reachable via `edgar.py` (8-K Item 2.02 Exhibit
99.1) but is NOT a substitute for the Q&A. Other residual gaps:
curated analyst-grade peer comp, supplier/customer ontology beyond
10-K Item 1, and hiring/patents/customs alt-data.

When a workflow needs a true gap item, lead the response with the
gap-disclosure pattern from `references/routing.md`:

> "To produce a publication-grade [X] I need [full Q&A transcript |
> curated comp group | …] which this skill set does not currently
> source. I can produce [partial deliverable with the data I do have] —
> or, if you paste the [transcript | comp group | …], I can do the
> full analysis."

Do NOT fabricate data, sketch what the analysis would look like, or
fall back to general knowledge. State the gap, then offer the partial.

---

## STEP 4 — Output

Produce the deliverable per the methodology doc, conforming to
`references/format.md`. End with a `Sources & References` block.

---

## File map

```
equity-research-flash/
├── SKILL.md                    ← this dispatcher
├── scripts/
│   ├── edgar.py                ← SEC EDGAR fetcher (10-K/Q/8-K/DEF 14A/S-1/13F/Form 4/13G/13D + XBRL Frames)
│   └── usaspending.py          ← Federal contract awards (api.usaspending.gov)
├── references/
│   ├── format.md               ← universal output spec (always read)
│   ├── routing.md              ← data → workspace-skill mapping + data gaps (always read on first invocation)
│   ├── discover.md             ← category dispatcher
│   ├── analyze.md              ← category dispatcher
│   ├── monitor.md              ← category dispatcher
│   ├── macro.md                ← category dispatcher
│   ├── anthropic/              ← Apache 2.0 vendored from anthropics/financial-services
│   │   ├── NOTICE.md           ← attribution + commit pin
│   │   ├── LICENSE             ← Apache 2.0
│   │   ├── catalyst-calendar/WORKFLOW.md
│   │   ├── earnings-analysis/WORKFLOW.md
│   │   ├── earnings-preview/WORKFLOW.md
│   │   ├── idea-generation/WORKFLOW.md
│   │   ├── initiating-coverage/WORKFLOW.md
│   │   ├── model-update/WORKFLOW.md
│   │   ├── morning-note/WORKFLOW.md
│   │   ├── sector-overview/WORKFLOW.md
│   │   └── thesis-tracker/WORKFLOW.md
│   └── community/              ← Apache 2.0 vendored from prof-little-bear/cc-equity-research
│       ├── NOTICE.md           ← attribution + commit pin + skipped list
│       ├── themes.md
│       ├── business-model.md
│       ├── earnings-scorecard.md
│       ├── financial-forensics.md
│       ├── reporting-quality.md
│       ├── management.md
│       ├── watchlist.md
│       ├── thesis-check.md
│       ├── event-radar.md
│       ├── yield-curve.md
│       └── labor-market.md
```

The nested workflow files inside `references/anthropic/<name>/` are
named `WORKFLOW.md` (not `SKILL.md`) so that opencode's recursive
`**/SKILL.md` discovery does not surface them as peer skills. Claude
Code's discovery is one-level and never saw them anyway. They are
read as methodology references by the parent dispatcher.
