# options.py — advanced reference

Listed option chains via `yfinance`. Lazy-imported.

## What's covered

- US-listed equity options (stocks + ETFs)
- US index options on indices with listed options: SPX, NDX, RUT, VIX, DJX
  — pass with the Yahoo index symbol (`^SPX`, `^NDX`, `^RUT`, `^VIX`, `^DJX`)
- ETF options (`SPY`, `QQQ`, `IWM`, ...) — pass the ETF symbol directly
- HK / European stock options — yfinance does NOT carry these reliably; use
  the upstream broker's API instead.

## Subcommand semantics

### `expiries SYM`
Returns the list of listed expiry dates (`YYYY-MM-DD`). Order is
chronological. Empty list = no listed options for this symbol.

### `chain SYM [--expiry YYYY-MM-DD] [--strike-range LO:HI]`
Default expiry = the nearest listed.

Returned schema per row (calls + puts):
- `contractSymbol` — OCC symbol (`AAPL260619C00200000` = AAPL 2026-06-19 $200 call)
- `lastTradeDate` — UTC timestamp
- `strike`, `lastPrice`, `bid`, `ask`, `change`, `percentChange`
- `volume`, `openInterest`
- `impliedVolatility` — annualized, decimal (0.25 = 25%)
- `inTheMoney` — bool
- `contractSize` — usually `"REGULAR"` (100 shares); `"MINI"` for old mini-options
- `currency`

Note yfinance does NOT return Greeks; only `impliedVolatility`. To compute
deltas/gammas, use Black–Scholes locally with `impliedVolatility`, spot,
strike, time-to-expiry, risk-free rate (from `macro-rates-fx/rates.py`),
and dividend yield (from `research.py info`).

`--strike-range LO:HI` filters to strikes between LO and HI inclusive.

### `quote SYM EXPIRY STRIKE TYPE`
Single-contract pull. `TYPE` = `C` or `P`. If the strike isn't listed, returns
nearest 10 strikes within ±50 of the requested strike for guidance.

### `iv-snapshot SYM [--limit N]`
ATM IV across all listed expiries. Strike closest to spot; uses **call IV**
(puts agree under put-call parity in normal regimes). Returns one row per
expiry with `atm_strike`, `call_iv`, `call_volume`, `call_oi`.

Useful for term-structure plotting / vol-surface bootstrap.

## Throttle

Yahoo rate-limits options endpoints harder than the chart endpoint.
yfinance internally caches some calls. For batch IV-surface workflows
across many symbols, expect occasional gaps and pace requests.

## Index options gotcha

`uv run scripts/options.py expiries ^SPX` — note the literal `^` in the symbol.
Some shells need quoting: `'^SPX'`. Settlement and AM/PM expiry semantics
differ between SPX (mostly AM, PM weeklies exist) and SPXW (weekly PM); the
chain returns both intermixed — distinguish by `contractSymbol` (`SPX...`
vs `SPXW...`).

## When to bypass this skill

For real-time tick-level options data, IV surfaces with fitted smiles,
exchange feed-direct data, GEX (dealer gamma exposure) — none of these are
in scope here. Use Polygon / CBOE LiveVol / SpotGamma / etc. (all keyed).