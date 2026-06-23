# Sources catalogue — macro-rates-fx

Raw endpoint reference. Verified 2026-05-27. All keyless except FRED.

## home.treasury.gov — US Treasury daily rates

CSV per-month download. Reverse-engineered from
<https://home.treasury.gov/resource-center/data-chart-center/interest-rates>.

```
GET https://home.treasury.gov/resource-center/data-chart-center/
    interest-rates/daily-treasury-rates.csv/all/{YYYYMM}
    ?type=daily_treasury_yield_curve&field_tdr_date_value_month={YYYYMM}
```

Returns CSV with `Date` + 14 tenor columns. EOD updated ~5pm ET on business
days. 20 years of history available; tenor coverage varies (see rates.md).

Other CSV `type` values exist for bill rates, real yields, par yields —
not wired here.

## api.frankfurter.dev — FX (ECB reference rates)

```
GET /v1/latest?base=USD&symbols=EUR,JPY,...
GET /v1/{YYYY-MM-DD}..{YYYY-MM-DD}?base=...&symbols=...
GET /v1/currencies
```

Updated daily ~16:00 CET on ECB business days. ~30 currencies supported.
No metals, no crypto.

Self-hosted FOSS — no rate limit advertised, but be courteous.

## api.stlouisfed.org/fred — FRED economic series

Requires `FRED_API_KEY` env var.

```
GET /fred/series/observations?series_id=X&api_key=K&file_type=json
GET /fred/series?series_id=X&api_key=K&file_type=json
GET /fred/series/release?series_id=X&...
GET /fred/release/dates?release_id=N&...
```

Rate-limited to 120 req/min per key.

800,000+ series available. Common IDs hard-coded in `CATALOGUE` in
`scripts/series.py`. To find more, search at <https://fred.stlouisfed.org>.

## Evaluated alternatives

| Source | Verdict |
|---|---|
| ECB SDW (Statistical Data Warehouse) | Same FX data as Frankfurter, raw form, more complex. |
| openexchangerates.org / exchangerate.host | Both keyed now. |
| World Bank Open Data | No FX, mostly annual macro. Out of scope. |
| OECD Data | Multi-country macro, but slow + complex schema. Defer to FRED equivalents. |
| BLS API | US labor data, also free; FRED proxies the same series (`PAYEMS`, `UNRATE`, `CPIAUCSL`). Use FRED. |
| Eurostat | EU macro; not wired. |
| ONS (UK) | UK macro; not wired. |
| ECB Statistical Data Warehouse | EU rates + monetary aggregates; not wired. |