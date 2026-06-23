# indicators — reference

Indicators are computed by `pandas-ta`. The `_apply` dispatcher in
`scripts/ta.py` is the source of truth — this doc explains semantics
and return-column conventions.

## Spec parsing

`name[:p1[:p2[:p3]]]` — colon-delimited positional params.

```
ema:20           length=20
macd:8:21:5      fast=8, slow=21, signal=5
bbands:20:2      length=20, std=2.0
supertrend:10:3  length=10, multiplier=3.0
```

Floats are detected by presence of `.` in the param (e.g. `bbands:20:2.5`).

## Indicator catalogue

| Spec | Params | Default | Returns |
|---|---|---|---|
| `ema:LEN`            | length            | 20      | `ema_{LEN}` |
| `sma:LEN`            | length            | 20      | `sma_{LEN}` |
| `wma:LEN`            | length            | 20      | `wma_{LEN}` |
| `rsi:LEN`            | length            | 14      | `rsi_{LEN}` |
| `macd:FAST:SLOW:SIG` | 12,26,9           |         | `MACD_{f}_{s}_{sig}`, `MACDh_{...}` (histogram), `MACDs_{...}` (signal) |
| `bbands:LEN:STD`     | length, std       | 20, 2.0 | `BBL_{LEN}_{STD}` (lower), `BBM_{...}` (middle/SMA), `BBU_{...}` (upper), `BBB_{...}` (bandwidth), `BBP_{...}` (%b) |
| `atr:LEN`            | length            | 14      | `atr_{LEN}` |
| `adx:LEN`            | length            | 14      | `ADX_{LEN}`, `DMP_{LEN}` (+DI), `DMN_{LEN}` (-DI) |
| `stoch:K:D`          | k=14, d=3         |         | `STOCHk_{K}_{D}_{D}`, `STOCHd_{K}_{D}_{D}` |
| `stochrsi:LEN`       | length            | 14      | `STOCHRSIk_{...}`, `STOCHRSId_{...}` |
| `vwap`               | —                 |         | `vwap` (requires datetime index for session reset) |
| `supertrend:LEN:M`   | length, multiplier| 10, 3.0 | `SUPERT_{LEN}_{M}`, `SUPERTd_{...}` (direction +1/-1), `SUPERTl_{...}`, `SUPERTs_{...}` |
| `ichimoku`           | —                 |         | `ISA_9`, `ISB_26`, `ITS_9` (Tenkan), `IKS_26` (Kijun), `ICS_26` (Chikou) |
| `obv`                | —                 |         | `obv` (cumulative volume signed by price direction) |
| `mfi:LEN`            | length            | 14      | `mfi_{LEN}` |
| `cci:LEN`            | length            | 20      | `cci_{LEN}` |
| `willr:LEN`          | length            | 14      | `willr_{LEN}` |
| `roc:LEN`            | length            | 10      | `roc_{LEN}` |
| `cmf:LEN`            | length            | 20      | `cmf_{LEN}` |
| `psar`               | —                 |         | `PSARl_*`, `PSARs_*`, `PSARaf_*`, `PSARr_*` (long/short stops, accel factor, reversal flag) |
| `kdj:LEN`            | length            | 9       | `K_{LEN}_{D}`, `D_{LEN}_{D}`, `J_{LEN}_{D}` (some pandas-ta versions; falls back to `stoch` if not present) |
| `fib:LOOKBACK`       | lookback bars     | 100     | `fib_high`, `fib_236`, `fib_382`, `fib_500`, `fib_618`, `fib_786`, `fib_low`, `fib_pct_from_low` (0..1; <0 or >1 = broke out), `fib_window_bars` |

Many indicators return **multiple columns** as a DataFrame — the dispatcher promotes each column to a top-level key in the response. This is why `macd` produces `MACD_12_26_9`, `MACDh_12_26_9`, `MACDs_12_26_9` in the output.

## `snapshot` default set

```
ema:20, ema:50, ema:200, rsi:14, macd, bbands:20:2, atr:14,
stochrsi:14, adx:14, obv, cci:20
```

Override with `--indicators a,b,c`.

## Derived flags in `snapshot`

After computing, the script attaches a few quick reads to `flags`:

- `rsi_14_overbought` — RSI(14) > 70
- `rsi_14_oversold` — RSI(14) < 30
- `golden_cross_state` — `"above"` if EMA50 > EMA200 else `"below"` (only when both present)

Add more in `cmd_snapshot` if useful — keep it ≤ a handful so the agent gets a fast read without parsing arrays.

## Crosses

`crosses` detects bar-by-bar where series A transitions across series B. Direction:

- `a_up` — A was ≤ B, now > B (e.g. price crossing above MA200)
- `a_down` — A was ≥ B, now < B

The first series can be `close` (the close price array) or any indicator spec. Same for the second. For a "golden cross" use `ema:50,ema:200`. For "price reclaims 200MA" use `close,ema:200`.

## NaN / Inf handling

Leading bars in any rolling indicator are NaN until the lookback fills (e.g. EMA200 needs ~200 bars). These become `null` in the output. Inf/-Inf also become `null`.

## Lookback requirements

| Indicator | Bars needed for first non-null |
|---|---|
| EMA/SMA/WMA n | n |
| RSI n | n + 1 |
| MACD (12,26,9) | ~33 |
| BB n | n |
| ATR n | n + 1 |
| ADX n | ~2n |
| StochRSI n | 2n |
| Ichimoku | 52 (Senkou B span) |
| KDJ 9 | ~9 |
| OBV | 1 |

If your input is shorter than the lookback, the latest snapshot value will be `null` — fetch more bars.

## pandas-ta gotchas

- pandas-ta is **fork-of-a-fork** with intermittent breakage on new pandas/numpy. Pin in `pyproject.toml`.
- Some indicator names (`kdj`, `eri`, `vortex`) are version-dependent. The dispatcher catches and falls back where sensible.
- `vwap` strictly requires a DatetimeIndex for session boundaries; the script handles this by indexing the OHLCV with parsed `dt` before calling pta.
