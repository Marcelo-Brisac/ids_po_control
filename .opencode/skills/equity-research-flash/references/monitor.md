# monitor — tracked-position workflows

Ongoing monitoring of names the user is already following. Use when the
user has a set of tracked tickers (their watchlist or a thesis they
already hold) and wants to keep tabs on what's changed.

If they're picking ideas from scratch, switch to `discover.md`. If they
want a one-time deep diagnostic on a single name, switch to
`analyze.md`.

---

## Workflows

| Workflow | Doc | Use when the user wants… |
|---|---|---|
| **Catalyst calendar** | `anthropic/catalyst-calendar/WORKFLOW.md` | Forward-looking calendar of earnings dates, expected announcements, regulatory milestones, conferences |
| **Thesis tracker** | `anthropic/thesis-tracker/WORKFLOW.md` | Running ledger of confirms vs breaks against an active thesis |
| **Morning note** | `anthropic/morning-note/WORKFLOW.md` | Desk-style daily morning roundup across a tracked list |
| **Watchlist maintenance** | `community/watchlist.md` | Manage the user-maintained list of tickers + themes being tracked |
| **Thesis check** | `community/thesis-check.md` | Quarterly review — are the original reasons for owning still intact? |
| **Event radar** | `community/event-radar.md` | Material events since last review — 8-Ks, M&A, exec changes, secondary offerings |

---

## Workflow steps

1. **Confirm scope.** Which names, what window since the last check, what depth. Establish or reference the watchlist.
2. **Read the workflow doc** and follow it.
3. **Pull data via workspace skills.** Heavy on `global-markets` per-name calendars + news + holders + insider data. CN names use `cn-markets`. Macro overlays use `macro-rates-fx`.
4. **Mind the data gaps.** `event-radar` reads **material 8-Ks directly via `scripts/edgar.py`** (Items 1.01 / 2.01 / 2.05 / 4.02 / 5.02 / 8.01 — see `references/routing.md`). 10-Q / 10-K / DEF 14A text for `thesis-check` and similar are also fetchable the same way. The residual gap is **earnings-call transcripts** (full Q&A). When you need transcripts, lead with the gap-disclosure pattern from `references/routing.md` — partial deliverable + offer to do the full version if the user pastes the transcript.
5. **Output.** Always satisfy `references/format.md`. End with `Sources & References`.

---

## Anti-triggers

Same anti-pattern as `analyze.md` — do NOT escalate quick lookups into a
workflow:

- "is NKE up today" → `global-markets` quote
- "any news on NKE" → `global-markets` news headlines (direct)
- "what's coming up next week" without a specific tracked list → if user
  wants a calendar across all listings, `global-markets` earnings
  calendar; only spin up the `catalyst-calendar` workflow when the user
  has a specific name (or short list) and wants curated per-name detail
