# Sources catalogue — global-markets

Raw endpoint reference for the skill's wrappers. Verified 2026-05-27 from
a CN-routed network. All keyless except `yfinance` (which uses its own
crumb/cookie handling for Yahoo Finance internally).

## api.nasdaq.com — US stocks, ETFs

Reverse-engineered from `nasdaq.com`'s frontend. Lightly authenticated by a
User-Agent header (any browser UA works). Returns clean JSON with dollar-sign
formatted strings.

### Endpoints

| Path | Returns |
|---|---|
| `/api/quote/{SYM}/info?assetclass={stocks\|etf\|index}` | Last price, change, exchange, name |
| `/api/quote/{SYM}/historical?assetclass=...&fromdate=YYYY-MM-DD&todate=YYYY-MM-DD&limit=N` | Daily OHLCV (MM/DD/YYYY date format) |
| `/api/quote/{SYM}/chart?assetclass=...&fromdate=...&todate=...` | Intraday-ish chart points |
| `/api/screener/stocks?download=true` | Full stock list (~7000 rows) |

### Gotchas

- `assetclass` is **required**. Wrong value → empty `data`. The wrapper guesses
  `etf` from `US_ETF_HINTS` and falls back to `stocks`. Add new ETFs to that set
  if Nasdaq returns no data on a known ticker.
- `index` assetclass: SPX/NDX/DJI return `Symbol not exists`. Indices are not on
  this API. Use Eastmoney for indices.
- Numbers are USD strings: `"$308.33"`, `"48,000,706"`. Wrapper strips `$` and `,`.
- `lastTradeTimestamp` is a human string like `"May 26, 2026"`; not ISO. Don't
  parse — pass through.

## push2.eastmoney.com — indices + global stocks

The data source behind every Chinese finance app. `secid` format is
`<market>.<code>`. Keyless. CN- and US-reachable.

### Endpoints

| URL | Returns |
|---|---|
| `https://push2.eastmoney.com/api/qt/stock/get?secid={S}&fields={F}` | Realtime quote (single symbol) |
| `https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={S}&klt={K}&fqt={A}&end={YYYYMMDD}&lmt={N}&fields1=...&fields2=...` | K-line history |
| `https://searchapi.eastmoney.com/api/suggest/get?input={Q}&type=14&count={N}` | Search by name/code |

### `secid` market prefixes

| Prefix | Market |
|---|---|
| `0.` | Shenzhen A-share (000xxx, 300xxx — but **cn-equities** skill owns this) |
| `1.` | Shanghai A-share (600xxx — **cn-equities** owns) |
| `100.` | Major global indices (US/EU/HK) |
| `105.` | US Nasdaq |
| `106.` | US NYSE |
| `107.` | US AMEX / ETF |
| `116.` | HK |
| `133.` | Tokyo (TSE) |
| `155.` | London (LSE) |
| `196.` | Korea (KRX) |

### Verified index secids

| Index | secid |
|---|---|
| S&P 500 | `100.SPX` |
| Nasdaq 100 | `100.NDX` |
| Dow Jones | `100.DJIA` |
| Hang Seng | `100.HSI` |
| DAX | `100.GDAXI` |
| FTSE 100 | `100.FTSE` |
| Nikkei 225 | `100.N225` (verify before use) |

### `klt` (kline period)

| Value | Meaning |
|---|---|
| `1` | 1-minute |
| `5` | 5-minute |
| `15`, `30`, `60` | n-minute |
| `101` | Daily |
| `102` | Weekly |
| `103` | Monthly |

### `fqt` (adjustment)

| Value | Meaning |
|---|---|
| `0` | None |
| `1` | Forward-adjusted (default for analysis) |
| `2` | Backward-adjusted |

### `fields` codes (quote)

| Code | Meaning | Notes |
|---|---|---|
| `f43` | Last price | Integer; divide by `10^f59` |
| `f44` | High | Scaled |
| `f45` | Low | Scaled |
| `f46` | Open | Scaled |
| `f47` | Volume | Raw |
| `f48` | Amount | Raw, currency depends on market |
| `f57` | Symbol code | String |
| `f58` | Name | String, Chinese for CN/HK |
| `f59` | Price decimals (scale exponent) | US/HK=3, indices/A-share=2. **Use this, not f152.** |
| `f60` | Previous close | Scaled |
| `f152` | Display decimals (UI only) | **Do not use as scale** — it under-scales US/HK by 10x. |
| `f168` | Turnover rate | Basis points |
| `f169` | Change abs | Scaled |
| `f170` | Change pct | Basis points (divide by 100) |

The wrapper handles scaling automatically.

### `klines` row format (CSV string per bar)

```
date,open,close,high,low,volume,amount,amplitude_pct
```

Note: `close` is the **second** field, not third — easy to misorder.

## query1.finance.yahoo.com — chart endpoint (fallback)

Yahoo Finance's `v8/finance/chart` endpoint. Keyless, single-symbol per call
(no batch). Wired as fallback for indices, HK/JP/DE/KR quotes, US quotes,
and FX. Direct curl probes from shared-egress IPs (E2B / Cloudflare) often
return HTTP 429 "Too Many Requests" — but Python urllib calls from the same
sandbox often succeed; the throttle appears UA- or endpoint-pattern-aware.

### Endpoint

```
https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}?interval=1d&range=5d
```

`interval`: `1m`/`5m`/`15m`/`30m`/`60m`/`1d`/`1wk`/`1mo`.
`range`: `1d`/`5d`/`1mo`/`3mo`/`6mo`/`1y`/`2y`/`5y`/`max`.

### Symbol conventions

| Market | Yahoo format | Example |
|---|---|---|
| US stock/ETF | bare | `AAPL`, `SPY` |
| HK | `{code}.HK` (drop leading 0 → 4 digits) | `0700.HK` (from `00700`) |
| Tokyo | `{code}.T` | `7203.T` |
| London | `{code}.L` | `BMW.L` |
| Korea | `{code}.KS` | `005930.KS` |
| Frankfurt | `{code}.DE` | `BMW.DE` |
| Major indices | `^{symbol}` | `^GSPC` (S&P 500), `^NDX`, `^DJI`, `^HSI`, `^GDAXI`, `^FTSE`, `^N225`, `^RUT`, `^HSCE`, `^HSTECH` |
| FX | `{BASE}{TARGET}=X` | `EURUSD=X`, `USDCNY=X` |
| Futures | `{code}=F` | `GC=F` (gold), `CL=F` (oil) |
| Crypto | `{coin}-USD` | `BTC-USD` |

### Response shape

```json
{
  "chart": {
    "result": [{
      "meta": {"symbol": "...", "regularMarketPrice": ..., "chartPreviousClose": ..., "currency": "USD", ...},
      "timestamp": [unix, unix, ...],
      "indicators": {"quote": [{"open": [...], "high": [...], "low": [...], "close": [...], "volume": [...]}]}
    }],
    "error": null
  }
}
```

`meta.regularMarketPrice` is the last price. `meta.chartPreviousClose` is
previous close. Day OHLC are in `meta.regularMarketDay{High,Low}` — Yahoo
omits a separate `open` in `meta`, so the wrapper uses the high as a
placeholder (intentionally lossy; pull from `indicators.quote[0]` for
precise OHLC).

### Gotchas

- **No batch.** Each symbol = one HTTP. For multi-symbol Yahoo calls, loop;
  there is no equivalent of v7/quote's `symbols=` without a crumb.
- **HK leading-zero strip.** Yahoo expects `0700.HK`, not `00700.HK`. The
  wrapper auto-normalizes from Eastmoney `116.00700`.
- **Indices use `^` prefix** including for HSI (`^HSI`, not `HSI`).
- **429 throttle.** Treat as soft failure; do not retry tight (just makes it
  worse). Wrapper returns `None` from the helper and the caller's chain
  continues to the next provider.
- **`v7/finance/quote` requires a crumb** (scraped from a browser-loaded
  page) since 2023. Not wired — too brittle.

## api.frankfurter.dev — FX (ECB reference rates)

Open-source service, ECB-sourced, free, no rate limit documented. 30+ G10 + CNY
+ several EM currencies. Updates once per business day around 16:00 CET.

### Endpoints

| Path | Returns |
|---|---|
| `/v1/latest?base=USD&symbols=EUR,JPY,CNY` | Today's rate |
| `/v1/{YYYY-MM-DD}?base=USD&symbols=EUR` | Single historical day |
| `/v1/{FROM}..{TO}?base=USD&symbols=EUR,CNY` | Date-range timeseries |
| `/v1/currencies` | Currency list |

### Gotchas

- The legacy `api.frankfurter.app` returns 301 to `api.frankfurter.dev`. Use
  `.dev` directly — saves a redirect.
- Weekends/holidays: missing dates are silently omitted from timeseries.
- Currency must be uppercase 3-letter ISO 4217.

## Rate limits

None of the providers publish rate limits; the following thresholds are
empirical.

- **Eastmoney (`push2*.eastmoney.com`)** — undocumented per-IP burst ceiling.
  Symptom when tripped: HTTPS connect succeeds but the server closes the
  socket before sending a response (`RemoteDisconnected` from urllib,
  `Empty reply from server` / curl exit 52). Affects subsequent calls from
  the same IP for several minutes; reproducible from both Python and curl.
  Observed at roughly 20 calls in 5 seconds. Affects indices and the
  HK/JP/DE/KR stock path (no fallback). Wrapper retries (`http_text`
  attempts 3× with backoff) don't help once blackholed; pacing does.
- **Nasdaq (`api.nasdaq.com`)** — uncharacterized; no block observed in
  normal use.
- **Frankfurter (`api.frankfurter.dev`)** — uncharacterized; ECB-backed,
  expected to be generous.

## Evaluated alternative sources (not wired)

Verified 2026-05-27. None wired into the v1 wrapper. Listed here so future
work doesn't re-evaluate them from scratch.

### US equities

| Source | Endpoint | Auth | Status |
|---|---|---|---|
| Yahoo Finance (used) | `query1.finance.yahoo.com/v8/finance/chart/{SYM}` | none | Wired as fallback (see section above). v7 batched quote needs crumb — not wired. |
| Stooq | `stooq.com/q/d/l/?s={sym}&i=d` (history), `stooq.com/q/l/?s=...&f=...` (quote) | API key (free, requires CAPTCHA + email) | Was keyless pre-2026, now gated. |
| Alpha Vantage | `alphavantage.co/query?function=GLOBAL_QUOTE&symbol=...` | API key (free tier 25 req/day) | Keyless calls return HTTP 200 with `"Note": "..."` body. |
| Polygon | `api.polygon.io/v2/...` | API key (free tier 5 req/min) | — |
| Tiingo | `api.tiingo.com/iex/{sym}` | API key (free tier) | — |
| Finnhub | `finnhub.io/api/v1/quote?symbol=...` | API key (free tier 60 req/min) | — |
| IEX Cloud | `cloud.iexapis.com/stable/...` | API key | Service discontinued Aug 2024. |
| Twelve Data | `api.twelvedata.com/quote?symbol=...` | API key | — |

### FX

| Source | Endpoint | Auth | Status |
|---|---|---|---|
| exchangerate.host | `api.exchangerate.host/latest?base=USD&symbols=EUR` | API access_key (was keyless pre-2025) | Now returns `{"success":false,"error":{"code":101,"type":"missing_access_key"}}`. |
| Open Exchange Rates | `openexchangerates.org/api/latest.json?app_id=...` | App ID required | — |
| ExchangeRate-API | `v6.exchangerate-api.com/v6/{key}/latest/USD` | API key | Free tier exists. |
| Fixer.io | `data.fixer.io/api/latest?access_key=...` | API key | — |
| Currencylayer | `api.currencylayer.com/live?access_key=...` | API key | — |
| ECB SDW direct | `data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?lastNObservations=1&format=jsondata` | none | Verified working keyless. SDMX JSON format (heavier than Frankfurter). |
| Frankfurter (used) | `api.frankfurter.dev/v1/...` | none | Primary in v1. |

### CN-specific (covered by `cn-equities`)

| Source | Endpoint | Auth | Status |
|---|---|---|---|
| Tencent (`qt.gtimg.cn`) | `qt.gtimg.cn/q=sh600519,sz000001,hk00700` | none | Verified. Batched CSV (GBK). Used as third-tier fallback in `cn-equities`. |
| AKShare (Python lib) | wraps Eastmoney + Sina + Tencent + 同花顺 + JuChao + many others | none | Library only; the underlying endpoints it calls are individually addressable. |
| 同花顺 (10jqka) | `d.10jqka.com.cn/v6/realhead/hs_{code}/last.js` | none | CN-IP friendly, occasional UA gating. |
| JuChao (cninfo) | `webapi.cninfo.com.cn/api/stock/...` | none | Announcements + filings, not realtime quotes. |

### Crypto (deferred to its own skill)

| Source | Endpoint | Auth | Status |
|---|---|---|---|
| blockstream.info | `blockstream.info/api/blocks/tip/height` etc. | none | Verified. BTC chain only. |
| CoinGecko | `api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd` | API key (Demo plan: keyless but rate-limited 30/min) | — |
| Binance public | `api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT` | none | Geo-blocked from US. |
| OKX public | `okx.com/api/v5/market/ticker?instId=BTC-USDT` | none | — |
| Coinbase Exchange | `api.exchange.coinbase.com/products/BTC-USD/ticker` | none | US-friendly. |
| Kraken | `api.kraken.com/0/public/Ticker?pair=XBTUSD` | none | — |

### Macro / rates (deferred to `macro-rates-fx`)

| Source | Endpoint | Auth | Status |
|---|---|---|---|
| FRED | `api.stlouisfed.org/fred/series/observations?series_id=...&api_key=...` | API key (free, instant) | Primary planned for `macro-rates-fx`. |
| Treasury Direct CSV | `home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/...` | none | Verified. Keyless Treasury yields CSV. |
| BLS public XML | `bls.gov/pub/time.series/...` | none | Akamai blocks scripted UA on CGI paths; pub flat files work with proper UA. |
| ECB SDW | (see FX section) | none | Macro series available via different flow IDs. |

## Backlog (v2)

Things considered for v1 but deferred:

| Need | Why deferred |
|---|---|
| **VIX** | Eastmoney `100.VIX` returns null. No keyless source survives. |
| **Futures (GC, CL, HG, etc.)** | Same — Eastmoney futures secids return null. CME quotes need a key. |
| **Intraday US bars** | Eastmoney has `klt=1/5/15`, but for US tickers it's 15-min delayed and timezone-confusing. Skip until someone asks. |
| **Options chains** | Big surface area; out of scope. |
| **Pre/post-market** | Nasdaq API only returns regular session. |
| **Stock fundamentals (P/E, market cap, earnings)** | Different API surface. Could be its own skill (`equity-fundamentals`). |

## Cross-reference

- `cn-equities` skill — owns Shenzhen/Shanghai A-shares + HK (`0.*`, `1.*`, `116.*` secids).
- `macro-rates-fx` skill — owns US Treasury yields, CPI, NFP (FRED-backed).
- `news-briefing` skill (deferred) — owns financial news RSS.
