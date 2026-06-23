# analyze — single-name deep-dive workflows

Multi-turn analytical workflows on **one company at a time**. Use when
the user has a specific ticker and wants depth — initiation note,
earnings deep-dive, forensic check, model update, business-model
diagnosis, management/comp review, reporting-quality audit, or
earnings-call scorecard.

If the user is comparing several names, looking for ideas, or scanning a
sector, switch to `discover.md`. If they have an established position
and want to track it over time, switch to `monitor.md`.

---

## Workflows

### Heavy, multi-task, multi-deliverable (Anthropic bundle)

| Workflow | Doc | Output | Typical turns |
|---|---|---|---|
| **Initiation note** | `anthropic/initiating-coverage/WORKFLOW.md` | 5 separately-invoked tasks: research doc → financial model (.xlsx) → valuation analysis → 25-35 charts (.zip) → 30-50 page DOCX report | 5+ user requests |
| **Earnings preview** | `anthropic/earnings-preview/WORKFLOW.md` | Pre-print setup: what to watch on the call | 1-2 |
| **Earnings analysis** | `anthropic/earnings-analysis/WORKFLOW.md` | Post-print update: 8-12 page DOCX | 2-3 |
| **Model update** | `anthropic/model-update/WORKFLOW.md` | Existing model refreshed with latest data | 1-2 |

### Light, single-deliverable (community lenses)

| Workflow | Doc | What it produces |
|---|---|---|
| **Business-model diagnosis** | `community/business-model.md` | How company makes money, customer-retention picture, pivot signals |
| **Earnings-call scorecard** | `community/earnings-scorecard.md` | Quantitative + qualitative scoring of a call |
| **Financial forensics** | `community/financial-forensics.md` | Six-pattern quality-of-earnings check (FCF/NI gap, SBC, channel-stuffing, non-GAAP gap, working-cap, capitalization) |
| **Reporting-quality audit** | `community/reporting-quality.md` | Metric definition drift, SEC cross-checks, selective omission |
| **Management review** | `community/management.md` | Capital allocation track record, comp, insider patterns |

---

## Workflow steps

1. **Confirm scope before reading any methodology doc.** Restate (a) ticker, (b) which workflow, (c) expected deliverables, (d) expected turn count. Especially important for the Anthropic bundle — `initiating-coverage` is FIVE separately-invoked tasks that need explicit user requests for each. Do NOT silently kick off a 5-task pipeline because the user said "give me a deep dive on NKE".
2. **Read the workflow doc.** Open the matching `.md` from the tables above and follow it.
3. **Pull data via workspace skills.** See `references/routing.md`. Heavy reliance on `global-markets` (US fundamentals + estimates + insiders + holders + per-name calendar + options) or `cn-markets` (A-share fundamentals, 业绩预告, 龙虎榜, 大宗交易, 解禁).
4. **Mind the data gaps.** **SEC filings (10-K/Q/8-K/DEF 14A/etc.) ARE sourced** via `scripts/edgar.py` — use it for `financial-forensics`, `reporting-quality`, `business-model`, `management`, and any workflow that wants filing text. The residual gap for this category is **earnings-call transcripts** (full Q&A) used by `earnings-preview`, `earnings-analysis`, `earnings-scorecard`. When you hit a transcript-only step, lead with the gap-disclosure pattern from `references/routing.md` — partial deliverable + offer to do the full version if the user pastes the transcript.
5. **Output.** Always satisfy `references/format.md`. End with `Sources & References`.

---

## Anti-triggers (do NOT load a workflow for these)

These belong to the workspace's market-data skills, not here:

- "what's NKE trading at" → `global-markets` quote
- "show me NKE's P&L" → `global-markets` fundamentals snapshot
- "who owns NKE" → `global-markets` holders snapshot
- "NKE insider transactions" → `global-markets` insiders snapshot
- "options on NKE" → `global-markets` chain
- "NKE next earnings date" → `global-markets` per-name calendar

These are direct snapshot calls. Don't wrap them in a multi-step
analytical workflow.
