# discover — idea generation workflows

Idea-generation workflows. Use when the user wants to find new names or
sectors to look at, not when they have a specific name in mind.

If the user already has a single ticker and wants depth on it, switch to
`analyze.md`. If they have a list of names already and want to track them
over time, switch to `monitor.md`.

---

## Workflows

| Workflow | Doc | Use when the user wants… |
|---|---|---|
| **Sector overview** | `anthropic/sector-overview/WORKFLOW.md` | State-of-play across an entire sector — what's working, what's broken, who's positioned |
| **Idea screen** | `anthropic/idea-generation/WORKFLOW.md` | Systematic quantitative + qualitative screen across a universe by lens (value, quality, growth, momentum, etc.) |
| **Theme read** | `community/themes.md` | "What's the market rewarding right now" — reading sector / factor returns and pulling tickers from inside the winning baskets |

---

## Workflow steps

1. **Confirm scope.** What universe (US large-cap? CN A-share? a specific sector?), what time window, what lens. If unclear, ask one question.
2. **Read the workflow doc.** Open the matching `.md` from the table above and follow its instructions.
3. **Pull data via workspace skills.** See `references/routing.md` — most discover workflows use `global-markets` (US fundamentals + estimates + earnings calendars) or `cn-markets` (A-share signals, 板块, 北向). Theme reads usually pull index/ETF returns to identify the winning baskets first.
4. **Output.** Always satisfy `references/format.md`. End with a `Sources & References` block.

---

## Data-gap awareness

**Federal contract awards ARE sourced** via `scripts/usaspending.py`
(see `references/routing.md`) — use it for any govtech / defense-prime
/ public-payor discovery, don't declare gov-contracts a gap. The
residual alt-data gap is **supplier ontology** and **customs flows**
(the upstream `supply-chain` and `trade-flows` community skills were
not vendored — see `community/NOTICE.md`). A chunk of
`idea-generation`'s screen lenses lean on these. If the user asks for
a supplier-chain-mapped or customs-flow discovery, say so up front
using the gap-disclosure pattern from `references/routing.md`.
