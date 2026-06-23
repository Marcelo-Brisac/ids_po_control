# macro — structural macro framing workflows

Multi-indicator macro-framing workflows. Use when the user wants a
*read* on the macro regime (rate cycle stance, labor cycle stance) that
combines multiple series into a verdict, not just a single number.

If the user wants a single FRED series or a quick yield/CPI lookup,
that's a direct `macro-rates-fx` call — don't load a workflow.

---

## Workflows

| Workflow | Doc | Use when the user wants… |
|---|---|---|
| **Yield-curve regime read** | `community/yield-curve.md` | Where the rate cycle is — inversion / re-steepening, recession-signal status, what the front-end vs long-end is saying |
| **Labor-market regime read** | `community/labor-market.md` | Leading labor indicators beyond the headline payroll number — jobless claims, ECI, JOLTS, AHE, participation — and what they say together |

(Note: this is the smallest category. The Anthropic bundle has no
macro skills, and the upstream `community/economic-research/trade-flows.md`
was skipped — see `references/community/NOTICE.md` — because it requires
HS-code customs-flow data the workspace doesn't yet source.)

---

## Workflow steps

1. **Confirm scope.** Which regime question, what window, what verdict shape (e.g. "are we in late-cycle?").
2. **Read the workflow doc** and follow it.
3. **Pull data via workspace skills.** Heavy reliance on `macro-rates-fx` (FRED series + US Treasury yield curve + ECB FX). FRED requires `FRED_API_KEY`.
4. **Output.** Always satisfy `references/format.md`. End with `Sources & References`.

---

## Anti-triggers

Single-number lookups should NOT load a workflow:

- "what's the 10-year at" → `macro-rates-fx` direct call
- "what was last CPI" → `macro-rates-fx` direct FRED series
- "show me the curve" → `macro-rates-fx` direct call

Workflows are only for *combining* multiple signals into a regime verdict.
