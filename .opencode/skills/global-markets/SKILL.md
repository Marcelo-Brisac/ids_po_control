---
name: global-markets
description: >
  Market-data lookups for global equities, ETFs, indices, FX, and futures
  — raw data retrieval only, no synthesis or attribution. Use when the
  user wants to retrieve: (1) a quote or price history for a stock, ETF,
  index, FX pair, or futures contract, (2) company fundamentals (income
  statement, balance sheet, cash flow), (3) options chains, IV term
  structure, or single-contract quotes, or (4) holders, insiders, analyst
  estimates, earnings calendar, dividend actions, or news headlines on a
  single name.
---

# Global Markets

Three scripts, three concerns. Price tape is stdlib-only and fast. Research +
options use `yfinance` (lazy-imported — only the path that needs it will fail
without it, with an install hint).

| Script | Deps | Covers |
|---|---|---|
| `scripts/equity.py`   | stdlib | US stocks/ETFs, global indices, FX, search, HK/JP/DE/KR via search |
| `scripts/futures.py`  | stdlib | 30 contracts — NYMEX/COMEX/NYBOT + CBOT grains + CME ES/NQ/YM via Eastmoney; CFE VX / CBOT rates / DX / RTY via Yahoo |
| `scripts/research.py` | `yfinance` | fundamentals, info, holders, insiders, recommendations, estimates, calendar, news, actions, ESG |
| `scripts/options.py`  | `yfinance` | listed option chains, expiries, single-contract quotes, IV term structure |

Install yfinance only if you'll use research or options:

```bash
# At the skill root (where pyproject.toml + uv.lock live)
uv sync --frozen       # one-time, installs exactly what's locked
```

`--frozen` skips re-resolution and installs straight from `uv.lock`
— fast and reproducible. If it errors with "lock out of date", the
maintainer needs to re-lock; don't drop `--frozen` to mask it.

**Always invoke yfinance-backed scripts via `uv run`** (`uv run
scripts/research.py …`). The shebang is plain `#!/usr/bin/env
python3`, so `./scripts/research.py` will pick the system
interpreter and fail with `yfinance not installed` even after
`uv sync`. Stdlib-only scripts (`equity.py`, `futures.py`) can be
run either way.

The scripts emit `{"error":"yfinance not installed","install":"..."}` on the
research/options paths when missing — other paths run unaffected.

## CLI

### equity.py (stdlib)

```bash
./scripts/equity.py quote SYM[,SYM,...]         # last price for US tickers
./scripts/equity.py index NAME[,NAME,...]       # SPX, NDX, DJI, HSI, DAX, RUT, FTSE, N225
./scripts/equity.py history SYM --days N        # daily OHLCV (also --from --to)
./scripts/equity.py search "QUERY"              # ticker by name (any market)
./scripts/equity.py fx FROM TO[,TO,...]         # latest FX rate(s)
./scripts/equity.py fx-history FROM TO --days N
```

Non-US tickers: pass Eastmoney `secid` (`116.00700` for Tencent HK, `133.7203` for Toyota TSE, ...) with `--source=eastmoney` to `quote`. `search` returns the secid for any name.

→ Symbol guide, source strategy, source fallback details: [references/equity.md](references/equity.md)

### futures.py (stdlib)

```bash
./scripts/futures.py quote ALIAS[,ALIAS,...]    # front-month quotes
./scripts/futures.py list                       # supported contract aliases
```

Common aliases: energy (`CL` `BZ` `NG` `RB` `HO`); metals (`GC` `SI` `HG` `PL` `PA`); soft (`SB` `CT` `KC` `CC`); grains (`ZC` `ZW` `ZS`); equity-index (`ES` `NQ` `YM` `RTY`); rates (`ZT` `ZF` `ZN` `ZB`); FX/vol (`DX` `VX`).

→ Full catalogue, continuous-month code conventions, exchange routing: [references/futures.md](references/futures.md)

### research.py (yfinance)

```bash
uv run scripts/research.py fundamentals SYM [--quarterly]   # IS + BS + CF
uv run scripts/research.py info SYM                         # company snapshot, ratios, margins
uv run scripts/research.py holders SYM                      # major + institutional + mutual fund
uv run scripts/research.py insiders SYM                     # transactions + roster + purchases
uv run scripts/research.py recommendations SYM              # analysts + upgrades/downgrades + targets
uv run scripts/research.py estimates SYM                    # EPS + revenue + growth + EPS trend
uv run scripts/research.py calendar SYM                     # next earnings + dividend dates
uv run scripts/research.py earnings-calendar [--start --end --symbols --limit]  # window scan across all US listings (stdlib — no yfinance needed)
uv run scripts/research.py news SYM [--limit N]             # Yahoo Finance headlines
uv run scripts/research.py actions SYM                      # dividend + split history
uv run scripts/research.py sustainability SYM               # ESG scores
```

→ Field semantics, response normalization, gotchas: [references/research.md](references/research.md)

### options.py (yfinance)

```bash
uv run scripts/options.py expiries SYM                              # listed expiry dates
uv run scripts/options.py chain SYM [--expiry YYYY-MM-DD] [--strike-range LO:HI]
uv run scripts/options.py quote SYM EXPIRY STRIKE TYPE              # single contract; TYPE = C or P
uv run scripts/options.py iv-snapshot SYM [--limit N]               # ATM IV term structure across expiries
```

→ Greeks, IV semantics, when `option_chain` is stale, index-options coverage: [references/options.md](references/options.md)

## Source strategy

| Need | Primary | Fallback |
|---|---|---|
| US stock/ETF quote + history | api.nasdaq.com | Yahoo (bare) → Eastmoney (`105./106./107.`) |
| Global indices | push2.eastmoney.com (`100.*`) | Yahoo (`^GSPC`, `^NDX`, `^DJI`, ...) |
| HK / JP / DE / KR stocks | push2.eastmoney.com (`116./133./155./196.`) | Yahoo (`0700.HK`, `7203.T`, ...) |
| FX | api.frankfurter.dev | Yahoo (`EURUSD=X`) |
| Futures NYMEX/COMEX/NYBOT (energy/metals/soft) | futsseapi.eastmoney.com (sc=101/102/108) | Yahoo (`=F`) |
| Futures CBOT grains (ZC/ZW/ZS/ZL/ZM) | futsseapi.eastmoney.com (sc=103) | Yahoo |
| Futures CME equity-index (ES/NQ/YM) | futsseapi.eastmoney.com (sc=103) | Yahoo |
| Futures CBOT rates (ZN/ZB/ZF/ZT), DX, RTY, CFE VX | Yahoo (`=F`) | — |
| Fundamentals / options / holders / news | Yahoo via `yfinance` | — |

→ Endpoint catalogue: [references/sources.md](references/sources.md)

## Rate limits

Eastmoney and Yahoo both throttle by IP with multi-minute windows.
On failure (RemoteDisconnected from Eastmoney; HTTP 429 / YFRateLimitError
from Yahoo), **don't retry** — return the error and move on.

## Notes

- All quote/history paths are keyless and stdlib-only — no install needed for the hot path.
- For mainland A-share / HK with CN-flavored signals (北向, 涨跌停, 行业/题材板块), use `cn-markets/scripts/equity.py` — it batches A-shares in a single HTTP.
