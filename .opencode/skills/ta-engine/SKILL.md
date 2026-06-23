---
name: ta-engine
description: >
  Technical-analysis indicator engine over an OHLCV array. Use when the
  user wants: (1) the full series of one or more indicators (EMA, SMA,
  RSI, MACD, Bollinger Bands, ATR, ADX, Stochastic, Ichimoku, VWAP,
  etc.), (2) a latest-bar snapshot with a curated default indicator set
  plus derived flags (overbought/oversold, trend, momentum), or (3)
  crossover detection between any two series.
---

# TA Engine

One script. One dep group (`pandas-ta` + `pandas` + `numpy`, lazy-imported).
Asset-agnostic — feed any OHLCV JSON.

## Install & invoke

```bash
# At the skill root (where pyproject.toml + uv.lock live)
uv sync --frozen                        # one-time, installs exactly what's locked
uv run scripts/ta.py <subcommand> ...   # always invoke via `uv run`
```

`--frozen` skips re-resolution and installs straight from `uv.lock`
— fast and reproducible. If it errors with "lock out of date", the
maintainer needs to re-lock; don't drop `--frozen` to mask it.

The script's shebang is plain `#!/usr/bin/env python3`, which picks
up the system interpreter and won't see the skill's `.venv`. **Always
run it through `uv run`** so pandas-ta is resolved from the local
`.venv`. Direct `./scripts/ta.py` will fail with `missing dep:
pandas_ta` even after `uv sync`.

`ta.py list` works without the deps installed (still invoke via
`uv run` for consistency; uv is a no-op if the env already exists).

## CLI

```bash
uv run scripts/ta.py list                                              # supported indicators (no deps)
uv run scripts/ta.py snapshot --input klines.json                      # latest-bar read on default set + flags
uv run scripts/ta.py snapshot -i - <<< "$(./other_skill ... klines)"   # via stdin
uv run scripts/ta.py compute --input klines.json --indicators rsi:14,macd,ema:50,ema:200,bbands:20:2
uv run scripts/ta.py crosses --input klines.json --series ema:50,ema:200    # golden/death-cross detection
uv run scripts/ta.py crosses --input klines.json --series close,ema:200     # price/200ma crosses
```

## Input shapes auto-detected

The script walks common container keys (`klines`, `history`, `series`,
`rows`, `data`, `ohlcv`) and accepts:

| Source | Shape |
|---|---|
| `crypto-markets/spot.py klines BTCUSDT ...` | `{"klines":[{"open":..,"high":..,"low":..,"close":..,"volume":..,"open_time":..},...]}` |
| `global-markets/equity.py history AAPL ...` | `{"history":[{"date":"YYYY-MM-DD","open":..,"high":..,"low":..,"close":..,"volume":..},...]}` |
| `cn-markets/equity.py history 600519 ...`    | `{"history":[{"date":"YYYY-MM-DD","open":..,"high":..,"low":..,"close":..,"volume":..},...]}` |
| Binance raw klines (list-of-lists)           | `[[open_time, o, h, l, c, v, close_time, ...], ...]` |
| Any list of dicts with OHLCV fields          | various key aliases supported (`o/h/l/c/v`, `Open/High/...`, `priceClose`, ...) |

→ Full key alias map: [references/input-shapes.md](references/input-shapes.md)

## Indicator spec syntax

`name[:param1[:param2[:param3]]]` — comma-separated for multiple.

```
ema:20            # 20-period EMA
sma:50            # 50-period SMA
rsi:14            # 14-period RSI
macd              # default 12/26/9
macd:8:21:5       # custom MACD
bbands:20:2       # 20-period BB, 2.0 std
atr:14            # 14-period ATR
adx:14            # ADX + +DI + -DI
stoch:14:3        # 14/3 Stochastic %K %D
stochrsi:14
vwap
supertrend:10:3
ichimoku          # Tenkan/Kijun/SenkouA/SenkouB/Chikou
obv               # cumulative
mfi:14
cci:20
willr:14
roc:10
cmf:20
psar
kdj:9             # falls back to stoch if not in pandas-ta version
fib:100           # Fibonacci retracement over last 100 bars (price levels + position)
```

→ Indicator family conventions, return-column names, length defaults: [references/indicators.md](references/indicators.md)

## Output

`compute`: arrays aligned to input bars. Length == `count`.
`snapshot`: scalar (latest bar) per indicator + derived `flags`
(rsi_14_overbought / rsi_14_oversold / golden_cross_state).
`crosses`: list of bars where series A crossed B (direction = a_up | a_down).

NaN/Inf values normalized to `null`. Floats rounded to 6 decimals.

## Pipeline pattern

```bash
# Crypto: BTC 4h klines -> TA snapshot
./crypto-markets/scripts/spot.py klines BTCUSDT --interval 4h --limit 300 \
  | (cd ./ta-engine && uv run scripts/ta.py snapshot -i -)

# Equity: AAPL daily history -> golden cross detector
./global-markets/scripts/equity.py history AAPL --days 365 \
  | (cd ./ta-engine && uv run scripts/ta.py crosses -i - --series ema:50,ema:200)

# A-share: 茅台 1y -> custom indicator set
./cn-markets/scripts/equity.py history 600519 --days 365 \
  | (cd ./ta-engine && uv run scripts/ta.py compute -i - --indicators rsi:14,macd,supertrend:10:3)
```
