# series.py — advanced reference

FRED economic series via St Louis Fed API. Requires `FRED_API_KEY`.

## Setup

1. Register a free account at <https://fredaccount.stlouisfed.org/>
2. Request an API key at <https://fred.stlouisfed.org/docs/api/api_key.html>
3. Export it: `export FRED_API_KEY=your_key_here`

Add to your shell profile to persist.

## Endpoints

```
https://api.stlouisfed.org/fred/series/observations?series_id=X&api_key=K&file_type=json
https://api.stlouisfed.org/fred/series?series_id=X&...
https://api.stlouisfed.org/fred/series/release?series_id=X&...
https://api.stlouisfed.org/fred/release/dates?release_id=N&...
```

## Subcommand semantics

### `series ID [--from --to]`
Full time series. `--from` / `--to` are `YYYY-MM-DD`. No date filters =
full available history (often 50+ years for major series).

### `latest ID`
Returns the latest observation **plus** the series metadata block (title,
units, frequency, seasonal adjustment). Useful when you don't know what
the series is.

### `release ID`
Shows which release publishes this series (e.g. CPIAUCSL is in "Consumer
Price Index") plus recent release dates. Use this for "when's the next
print?".

### `catalogue`
Prints the hard-coded common-IDs dict in the script. Edit
`scripts/series.py` `CATALOGUE` to extend.

## Rate limits

FRED limits to 120 requests/minute per API key. The script does not
backoff — burst-heavy agents should pace.

## Key series for macro workflows

### Recession monitoring
- `T10Y2Y` — 10Y-2Y spread (inversion warns)
- `T10Y3M` — 10Y-3M spread (Fed-preferred recession signal)
- `UNRATE` — unemployment rate (Sahm rule: ≥0.5pp rise of 3M MA over 12M low)
- `ICSA` — initial jobless claims (weekly, leading)
- `INDPRO` — industrial production (coincident)

### Inflation
- `CPIAUCSL` — headline CPI (level — compute YoY in agent)
- `CPILFESL` — core CPI
- `PCEPI` / `PCEPILFE` — PCE / core PCE (Fed's preferred)
- `PPIACO` — producer prices

### Fed policy
- `DFF` — Fed Funds effective rate (daily)
- `FEDFUNDS` — Fed Funds (monthly)
- `WALCL` — Fed balance sheet (Wednesday weekly)
- `M2SL` — M2 money stock

### Risk premia
- `BAMLH0A0HYM2` — US high-yield OAS (credit risk gauge)
- `BAMLC0A0CM` — US IG OAS
- `VIXCLS` — VIX close (equity vol)

### Trade / external
- `DTWEXBGS` — broad trade-weighted USD index

## Computing YoY / MoM

FRED returns levels for most series. For inflation rates:
```python
# CPI YoY:
yoy = series[-1].value / series[-13].value - 1.0
```
or use `units=pc1` URL parameter (not exposed by the wrapper; fetch
manually if you need it).

## Vintages

FRED supports "real-time" vintages (the values as known at a specific past
date — important for backtesting). Not exposed by this wrapper. Add a
`--realtime YYYY-MM-DD` flag if/when needed; the API param is
`realtime_start=` + `realtime_end=`.

## Cross-reference

For CN macro, see `cn-markets/scripts/macro.py`. Both skills deliberately
don't overlap.