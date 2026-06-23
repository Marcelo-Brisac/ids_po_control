# rates.py — advanced reference

US Treasury yield curve from Treasury Direct. Daily CSV, keyless, stdlib.

## Endpoint

```
https://home.treasury.gov/resource-center/data-chart-center/interest-rates/
  daily-treasury-rates.csv/all/{YYYYMM}
  ?type=daily_treasury_yield_curve
  &field_tdr_date_value_month={YYYYMM}
```

Returns CSV with header columns: `Date`, `1 Mo`, `1.5 Month`, `2 Mo`,
`3 Mo`, `4 Mo`, `6 Mo`, `1 Yr`, `2 Yr`, `3 Yr`, `5 Yr`, `7 Yr`, `10 Yr`,
`20 Yr`, `30 Yr`. One row per business day for the requested month.

Wrapper maps these to canonical keys: `1M`, `1.5M`, `2M`, `3M`, `4M`, `6M`,
`1Y`, `2Y`, `3Y`, `5Y`, `7Y`, `10Y`, `20Y`, `30Y`.

## Multi-month range

`series TENOR --from --to --` fetches one CSV per month spanned, dedups,
and returns sorted-desc by date. Cost: ceil((to-from)/30) HTTP requests.

## Cadence

Yields are updated each business day after market close (~5pm ET).
Treasury Direct does **not** publish weekend or holiday rows.

## `--date` semantics for `curve`

`curve --date YYYY-MM-DD` returns the **most recent row on or before** the
requested date. If you ask for a holiday or weekend, you get the prior
business day's curve.

## Tenor coverage

- `1M`, `1.5M`, `2M` — relatively new (added 2019); older months may be
  blank.
- `20Y` reintroduced 2020.
- `30Y` suspended Feb 2002 – Feb 2006 (blank in that window).

## Common derived series

The cash yield curve doesn't include spreads directly. Compute on the agent
side:
- 10Y-2Y spread = `curve["10Y"] - curve["2Y"]` (classic recession indicator)
- 10Y-3M spread = `curve["10Y"] - curve["3M"]` (Fed-watched)
- Curve steepness 2Y-30Y = `curve["30Y"] - curve["2Y"]`

For deeper time series of these spreads, use `series.py` FRED IDs
(`T10Y2Y`, `T10Y3M`).

## Alternatives evaluated

| Source | Verdict |
|---|---|
| FRED `DGS*` series | Same data, requires key. Treasury Direct preferred for keyless. |
| Wall Street Journal | HTML scrape, fragile. |
| Bloomberg / Refinitiv | Keyed. |
| treasury-rate.com (third party) | Stale; not authoritative. |