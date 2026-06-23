# input-shapes — reference

`ta.py` accepts JSON from `--input PATH` or `-i -` (stdin). It walks
the top-level dict for any of these container keys before treating
the payload as a list:

```
klines  history  series  rows  data  ohlcv
```

If the payload is already a list, it's used directly.

## Per-row shape

Each row can be either:

1. **List** (Binance raw kline):
   ```
   [open_time_ms, open, high, low, close, volume, close_time_ms, ...]
   ```

2. **Dict** with any of these key aliases per field:

| Field | Aliases (first-match wins) |
|---|---|
| open      | `open`, `o`, `Open`, `openPrice` |
| high      | `high`, `h`, `High`, `highPrice` |
| low       | `low`, `l`, `Low`, `lowPrice` |
| close     | `close`, `c`, `Close`, `closePrice`, `price` |
| volume    | `volume`, `v`, `Volume`, `vol` |
| timestamp | `open_time`, `close_time`, `timestamp`, `ts`, `time`, `date`, `datetime`, `Date`, `day` |

Missing OHLCV: if a row has only `close`, OHL are filled from close; volume defaults to 0.

## Timestamp handling

- Numeric > 1e12 → epoch ms (Binance / Eastmoney)
- Numeric ≤ 1e12 → epoch s
- String → parsed via `pandas.to_datetime` (handles ISO 8601 + most common formats)

Rows are sorted ascending by `dt` after parsing — many indicators assume time-ordered input. If timestamps are missing, the original order is preserved.

## Tested upstreams

These produce input that works out of the box:

- `cn-markets/scripts/equity.py history CODE --days N`
- `cn-markets/scripts/futures.py quote ALIAS` (single bar, but accepted)
- `global-markets/scripts/equity.py history SYM --days N`
- `crypto-markets/scripts/spot.py klines SYM --interval 1h --limit 300`
- Binance raw `/api/v3/klines` response (list-of-lists)

## Pre-flight check

```bash
echo '[{"close":100},{"close":101},{"close":99}]' | uv run scripts/ta.py snapshot -i -
```
Returns a snapshot of a minimal 3-bar series (most indicators will be `null` due to insufficient lookback).
