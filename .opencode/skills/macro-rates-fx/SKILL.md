---
name: macro-rates-fx
description: >
  Global macro, rates, and FX data lookups. Use when the user wants:
  (1) the US Treasury yield curve or per-tenor history (1M through 30Y),
  (2) FX latest snapshot or daily history (G10 plus 30+ minor
  currencies), or (3) a US economic series from FRED (CPI, PCE, NFP,
  unemployment, M2, Fed funds, recession indicators, OAS spreads, etc.)
  — requires FRED_API_KEY.
---

# Macro, Rates, FX

Three scripts. All stdlib. FRED requires a free API key in `FRED_API_KEY`.

| Script | Provider | Auth |
|---|---|---|
| `scripts/rates.py`  | home.treasury.gov daily CSV | none |
| `scripts/fx.py`     | api.frankfurter.dev (ECB reference rates) | none |
| `scripts/series.py` | api.stlouisfed.org/fred | `FRED_API_KEY` env var |

Get a free FRED key at <https://fred.stlouisfed.org/docs/api/api_key.html>.
Export it once:
```bash
export FRED_API_KEY=...
```

## CLI

### rates.py — US Treasury yield curve

```bash
./scripts/rates.py curve [--date YYYY-MM-DD]              # full curve for one day
./scripts/rates.py series TENOR [--from --to]             # one tenor over time
./scripts/rates.py recent [--days N]                      # recent N rows of the full curve
```

Tenors: `1M`, `1.5M`, `2M`, `3M`, `4M`, `6M`, `1Y`, `2Y`, `3Y`, `5Y`, `7Y`, `10Y`, `20Y`, `30Y`.

→ CSV layout, fetch strategy across month boundaries: [references/rates.md](references/rates.md)

### fx.py — Frankfurter (ECB reference rates)

```bash
./scripts/fx.py latest FROM TO[,TO,...]                   # snapshot, base→quotes
./scripts/fx.py history FROM TO --from --to               # daily series
./scripts/fx.py convert AMOUNT FROM TO                    # convert at latest rate
./scripts/fx.py symbols                                   # supported currencies
```

→ Coverage (no XAU/XAG/crypto), update cadence, weekend handling: [references/fx.md](references/fx.md)

### series.py — FRED economic series (needs key)

```bash
./scripts/series.py series ID [--from --to]               # full history of one series
./scripts/series.py latest ID                             # latest single observation
./scripts/series.py release ID                            # release schedule
./scripts/series.py catalogue                             # common series IDs and what they are
```

Common IDs:
- Inflation: `CPIAUCSL`, `CPILFESL` (core), `PCEPI`, `PCEPILFE` (core PCE)
- Labor: `UNRATE`, `PAYEMS` (NFP), `ICSA` (jobless claims), `AHETPI` (wages)
- Activity: `GDP`, `GDPC1` (real), `INDPRO`, `RSAFS`, `HOUST`, `DGORDER`
- Money / rates: `M2SL`, `WALCL` (Fed balance sheet), `DFF` (FF effective), `FEDFUNDS`
- Yields: `DGS10`, `DGS2`, `T10Y2Y`, `T10Y3M` (recession indicator)
- FX / Dollar: `DTWEXBGS` (trade-weighted broad), `DEXUSEU`, `DEXJPUS`
- Risk: `BAMLH0A0HYM2` (HY OAS), `BAMLC0A0CM` (IG OAS), `VIXCLS`
- Sentiment: `UMCSENT`

Run `catalogue` for the full list with descriptions.

→ Series metadata fields, release calendar, vintage data: [references/series.md](references/series.md)

## Source strategy

| Need | Provider | Notes |
|---|---|---|
| US Treasury yields (cash) | Treasury Direct daily CSV | EOD; updated ~5pm ET each business day |
| FX latest / history | Frankfurter (ECB reference) | EOD ECB fix at 16:00 CET; weekend = Friday's rate |
| FX intraday | — | not covered; bring your own (OANDA, Polygon, etc. all keyed) |
| Metals (XAU/XAG) | — | not covered by Frankfurter; use `global-markets` futures (`GC`, `SI`) for proxy |
| Crypto | — | use a dedicated crypto skill |
| US CPI / NFP / GDP / unemployment / Fed series | FRED | needs key |
| CN macro (CPI/PPI/GDP/M2/PMI/...) | — | lives in `cn-markets/scripts/macro.py` |

→ Endpoint catalogue: [references/sources.md](references/sources.md)

## Cross-reference

- `global-markets` — US Treasury **futures** (ZN/ZB/ZF/ZT) for hedging the cash curve.
- `cn-markets` — CN macro series + CN 国债收益率曲线 (different provider).
