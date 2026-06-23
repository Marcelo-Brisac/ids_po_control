# fx.py — advanced reference

Frankfurter (ECB reference rates) — daily EOD FX. Keyless, stdlib.

## Endpoint

```
https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR,JPY,GBP
https://api.frankfurter.dev/v1/{YYYY-MM-DD}..{YYYY-MM-DD}?base=USD&symbols=EUR
https://api.frankfurter.dev/v1/currencies
```

ECB publishes reference rates daily at ~16:00 CET (14:00 UTC) on business
days. **Weekends and ECB holidays** = the prior business day's rate.

## Coverage

G10: USD, EUR, GBP, JPY, CHF, AUD, CAD, NZD, SEK, NOK
+ DKK, ISK, PLN, HUF, CZK, RON, BGN, TRY, ILS, ZAR
+ AUD, NZD, IDR, INR, KRW, MYR, PHP, SGD, THB, CNY, HKD
+ MXN, BRL

**Not covered**:
- XAU / XAG / XPT / XPD (metals) — use `global-markets` futures (`GC`, `SI`, ...)
- Crypto — out of scope; use a crypto skill
- Synthetic crosses for currencies ECB doesn't publish (e.g. exotic African pairs)

Use `symbols` to fetch the live list.

## Cross-rate calculation

Frankfurter only accepts one `base` at a time, but `symbols` is a list. To
get cross-rates (e.g. EUR/JPY), use:
```bash
./scripts/fx.py latest EUR JPY
```
ECB publishes all majors against EUR; Frankfurter inverts when needed.

## Daily history

```bash
./scripts/fx.py history USD EUR --from 2020-01-01 --to 2026-05-27
```
Returns one rate per business day. Date range up to ~25 years; long
windows are large JSON (~10 KB/year/pair).

## Convert helper

```bash
./scripts/fx.py convert 1000 USD JPY
```
→ `{amount: 1000, rate: 159.21, result: 159210.0, date: 2026-05-26}`.

For multi-leg conversion (USD→XXX→YYY), do it in the agent.

## Update lag

If you query during the ECB rate-publication window (~14:00 UTC), you may
get the prior day's rate for a few minutes. Re-poll after 16:00 CET if
freshness matters.

## Alternatives evaluated

| Source | Verdict |
|---|---|
| ECB SDW JSON | Same data, more complex schema. Frankfurter is a clean wrapper. |
| openexchangerates.org | Keyed. |
| exchangerate.host | Was keyless; now requires `access_key`. |
| Yahoo `EURUSD=X` chart | Works, but Yahoo throttles. Frankfurter is more reliable for FX. |