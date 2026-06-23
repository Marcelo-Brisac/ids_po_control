# equity.py — advanced reference

Covers usage beyond the SKILL.md examples.

## Non-US tickers via `secid`

`equity.py quote` defaults to Nasdaq for bare tickers (`AAPL`, `MSFT`). For
anything outside the US (HK / JP / DE / KR / LSE), use Eastmoney's `secid`
format `<market>.<code>`:

| Prefix | Market | Example |
|---|---|---|
| `105.` | Nasdaq | `105.AAPL` (also works; Nasdaq direct is cleaner) |
| `106.` | NYSE | `106.IBM` |
| `107.` | AMEX / US ETF | `107.SPY` |
| `100.` | Major indices | `100.SPX`, `100.NDX`, `100.HSI`, `100.GDAXI` |
| `116.` | Hong Kong | `116.00700` (Tencent) |
| `133.` | Tokyo (TSE) | `133.7203` (Toyota) |
| `155.` | London (LSE) | `155.BARC` |
| `196.` | Korea (KRX) | `196.005930` (Samsung) |

```bash
./scripts/equity.py quote 116.00700 --source=eastmoney
```

When in doubt, use `search` — it returns the right `secid`.

## Source forcing

```bash
./scripts/equity.py quote AAPL --source=yahoo       # force Yahoo chart endpoint
./scripts/equity.py quote AAPL --source=eastmoney   # force EM 105.AAPL
```

Default `auto`: Nasdaq → Yahoo → Eastmoney chain.

## Index alias map

Friendly names resolved by `index`:

| Input | Resolved to |
|---|---|
| `SPX`, `S&P500`, `S&P 500` | EM `100.SPX` |
| `NDX`, `NASDAQ100`, `NASDAQ 100` | EM `100.NDX` |
| `DJI`, `DJIA`, `DOW` | EM `100.DJI` |
| `HSI`, `恒生指数` | EM `100.HSI` |
| `DAX`, `GDAXI` | EM `100.GDAXI` |
| `RUT`, `RUSSELL2000` | EM `100.RUT` |
| `FTSE`, `FTSE100` | EM `100.FTSE` |
| `N225`, `NIKKEI225` | EM `100.N225` |
| `HSCEI` | EM `100.HSCEI` (Yahoo fallback: `^HSCE`) |
| `HSTECH` | EM `100.HSTECH` |

Yahoo index symbols (`^GSPC` not `^SPX`, `^DJI` not `^DJIA`, `^GDAXI` not `^DAX`) are mapped in the fallback automatically.

## Yahoo HK leading-zero convention

Eastmoney `116.00700` → Yahoo `0700.HK` (strip leading zero from 5-digit
code, pad to 4-digit `.HK`). Wrapper handles this; relevant if you query
Yahoo directly.

## History `--from/--to/--days`

```bash
./scripts/equity.py history AAPL --from 2026-01-01 --to 2026-05-27
./scripts/equity.py history AAPL --days 30        # last 30 calendar days
```

Output is sorted newest-first.

## FX coverage

Frankfurter base list: G10 (USD, EUR, GBP, JPY, CHF, AUD, CAD, NZD, SEK, NOK)
+ many minors including CNY, HKD, SGD, INR, KRW, TRY, ZAR. **No metals**
(XAU/XAG) and **no crypto**. For metals, use `commodities` futures (`GC`/`SI`).

## Error envelope

Per-row structured errors when a row fails its chain:
```json
{"symbol": "FAKETICK", "error": "all sources failed"}
```
Other rows in the same batch still succeed.