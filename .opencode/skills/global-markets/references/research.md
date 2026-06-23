# research.py — advanced reference

`research.py` is a thin wrapper over `yfinance.Ticker(...)`. yfinance is
**lazy-imported**: scripts that don't call research-paths run without it.

## yfinance under the hood

yfinance scrapes Yahoo Finance. It handles cookie + crumb negotiation for
the authenticated `v7/finance/quote` and `query2.finance.yahoo.com/v10/`
endpoints internally — that's the main reason we don't roll our own.

For fundamentals statements (IS/BS/CF), yfinance returns ~4 quarters of
quarterly data and ~4 annual periods. For longer history, use SEC EDGAR
direct (planned `equity-fundamentals-deep` or call SEC EDGAR JSON manually).

## Response normalization

DataFrames are normalized to list-of-dicts with:
- Column labels stringified (Timestamps → `YYYY-MM-DD` slice).
- Index becomes the `field` key (so each row is `{field: ..., 2026-03-31: ..., 2025-12-31: ..., ...}`).
- NaN → `null`.

This is meant to be JSON-friendly, not human-readable. For human reading,
pipe through `jq` or render with pandas after parsing.

## Subcommand semantics

### `fundamentals SYM [--quarterly]`
Returns three top-level keys (`income_statement`, `balance_sheet`, `cash_flow`),
each a list-of-dicts. Field names match yfinance's internal labels
(`Total Revenue`, `Net Income`, `Operating Cash Flow`, ...) and are not
remapped — different Yahoo coverage tiers expose slightly different fields.

### `info SYM`
Cherry-picks the most useful ~50 fields from yfinance's `.info` dict
(which has 100+ noisy fields). If you need a field not in the picked set,
the agent can call yfinance directly:
```python
import yfinance as yf
print(yf.Ticker("AAPL").info)
```

### `holders SYM`
Three groups: `major_holders` (% breakdown), `institutional_holders` (top 10
institutions with shares/value/% out), `mutualfund_holders` (top 10 funds).

### `insiders SYM`
`transactions` (raw trades), `roster_holders` (officers + directors),
`purchases` (recent open-market purchases, often the most-watched).

### `recommendations SYM`
Buy/hold/sell ratings histogram by month; `upgrades_downgrades` is the
chronological action log; `analyst_price_targets` is a single-row consensus.

### `estimates SYM`
Forward-looking analyst data. Each subkey is a separate DataFrame:
- `earnings_estimate` — current Q + next Q + current Y + next Y EPS estimates
- `revenue_estimate` — same periods, revenue
- `earnings_history` — past 4 quarters of estimate vs actual + surprise %
- `eps_trend` — how the consensus has moved over the past 90 days
- `eps_revisions` — up/down revisions in the past 7/30 days
- `growth_estimates` — long-term growth rate consensus

### `calendar SYM`
Next earnings date, EPS estimate range, dividend date if applicable.
Returned as a dict (yfinance ≥0.2.40) or a 1-row DataFrame (older versions).

### `news SYM [--limit N]`
Normalized headlines: `title`, `summary`, `publisher`, `pubDate`, `url`,
`type`. The yfinance shape changed in 0.2.40 (wrap in `content` dict);
wrapper handles both.

### `actions SYM`
`dividends` (date + amount), `splits` (date + ratio), `capital_gains`
(funds only).

### `sustainability SYM`
ESG total + environment + social + governance scores. Often empty for
small caps.

## Gotchas

- **HK / TSE / DE / KS / KR symbols** work but with reduced coverage —
  fundamentals statements often partial.
- **ETFs** return useful `info` and `actions` but no IS/BS/CF (no company to
  report).
- **Yahoo rate-limits aggressively**. yfinance retries internally; in burst
  workflows space calls out or accept partial failure.
- **`.calendar` shape varies** by yfinance version. Wrapper handles dict +
  DataFrame; new shapes may surface as `null`.
- **News URL field** sometimes empty; Yahoo doesn't always return a
  canonical link.

## Cross-skill

For CN A-share fundamentals + events + ETF + 可转债, use
`cn-markets/scripts/research.py` (AKShare-backed). No overlap.