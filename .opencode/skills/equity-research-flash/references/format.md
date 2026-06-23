# Deliverable format — universal floor

Universal rules for any deliverable produced by this skill — report,
list, calendar, scorecard, model memo, screen output, anything. The
*shape* of the deliverable belongs to the workflow doc; the rules below
are the floor that applies regardless.

Adapted from `prof-little-bear/cc-equity-research`'s `FORMAT.md`
(Apache 2.0).

---

## 1. Quantify everything

The single highest-leverage rule. "Strong" means nothing; "$150M beat on
$1.2B revenue (+12.5%)" is clear.

- **Beat / miss / change** → always paired with $ and % (e.g., "beat by $60M, +2.5%")
- **YoY / QoQ deltas** → both absolute and percent where space allows
- **Margin moves** → in basis points ("GPM −430 bps to 40.2%")
- **Time period** → always stated (Q3'24A, FY26E, TTM, LTM)
- **Old vs. new** → when revising a number, show prior and new with the Δ

No "strong performance," "robust growth," or "meaningful improvement"
without numbers. No naked percentages without the dollar base.

---

## 2. Year notation

`A` for actual, `E` for estimate. Examples: `Q3'24A`, `FY26E`, `Q1'27E`.
Use them consistently on every period reference. The reader should never
have to guess whether a number is real or forecast.

---

## 3. Citations

Every number is a claim; every claim should be traceable.

- **SEC filings:** name the filing type, date, and section. Example:
  *NIKE Q3'26 10-Q filed 2026-04-01, MD&A.*
- **Earnings calls:** name speaker and whether prepared remarks or Q&A.
  Example: *Q3 FY26 call, CFO Friend in Q&A.*
- **Data pulled via workspace skills** (`global-markets`, `cn-markets`,
  `macro-rates-fx`, `crypto-markets`): cite the upstream the skill
  actually used — *Yahoo via yfinance*, *FRED series CPIAUCSL*,
  *Eastmoney F10 via akshare*, etc. The skill's own `references/` docs
  list the provider chain.
- **Combined sources:** name them all.

Forensic claims ("X never mentioned on the call", "Y disclosure dropped
in Q[Z]") need the *exact* document and section. Traceability is what
makes the catch credible.

---

## 4. Sources & References block

Every deliverable, no matter the shape, ends with a
`Sources & References` block listing the data, filings, and transcripts
actually used. Format:

```
---

## Sources & References

**Market data:** Yahoo via yfinance (global-markets skill); FRED series
[ID] (macro-rates-fx skill); etc.

**SEC filings:**
- [Company] FY24 10-K filed YYYY-MM-DD
- [Company] Q1'26 10-Q filed YYYY-MM-DD

**Earnings calls / other:**
- [Company] Q[X]'[YY] earnings call transcript, YYYY-MM-DD
```

The cheapest format upgrade in the guide and the one most often skipped.
Don't skip it.

---

## 5. Tone

- Institutional. Lead with numbers. Active voice. Short sentences.
- "vs." not "versus."
- No exclamation marks, no hype words ("incredible", "massive",
  "game-changing"), no emojis.
- Specific > generic. The reader is an analyst, not a beginner.

---

## 6. Tables

When presenting tables, auto-wrap cell content to preserve the table's
shape on screen whenever possible. A table that breaks into a ragged
column-of-stacked-text is unreadable.

- Keep cell text short enough that rows don't blow up vertically. If a
  cell needs a paragraph, the table is the wrong shape — move that
  content to bullets below the table.
- Prefer fewer wider columns over many narrow ones. 3–5 columns is the
  sweet spot; 6+ usually wraps badly on standard terminal widths.
- Use compact phrasing inside cells (no full sentences when a fragment
  works), and trim redundant words ("the", "that", "which") aggressively.
- If a column needs long content (e.g., a thesis paragraph), pull it
  out as a footnote-style bullet keyed to a short tag in the table.

The goal is shape preservation: a reader scanning the table should be
able to read down a column without their eye jumping rows.

---

## What this guide does NOT cover

The structure of the deliverable — top-of-doc box, bullet style,
section ordering — is the workflow doc's call. A `catalyst-calendar` is
a calendar, an `earnings-analysis` is a report, a `watchlist` is a
tracked list. Each workflow doc prescribes its own shape. The rules
above are what every deliverable owes the reader regardless.
