# derivatives.py — reference

Perpetual funding / open interest / long-short ratios from Binance,
Bybit, and OKX public endpoints. All keyless.

## Endpoints

```
# Binance (linear USDT-margined)
GET https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT
GET https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=30
GET https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT
GET https://fapi.binance.com/futures/data/{globalLongShortAccountRatio,topLongShortAccountRatio,topLongShortPositionRatio,takerlongshortRatio}?symbol=BTCUSDT&period=1h&limit=30

# Bybit (linear)
GET https://api.bybit.com/v5/market/tickers?category=linear&symbol=BTCUSDT
GET https://api.bybit.com/v5/market/funding/history?category=linear&symbol=BTCUSDT&limit=30
GET https://api.bybit.com/v5/market/open-interest?category=linear&symbol=BTCUSDT&intervalTime=5min&limit=1

# OKX (swap)
GET https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP
GET https://www.okx.com/api/v5/public/funding-rate-history?instId=BTC-USDT-SWAP&limit=30
GET https://www.okx.com/api/v5/public/open-interest?instType=SWAP&instId=BTC-USDT-SWAP
```

## Symbol translation

`funding/oi` accept a Binance-style pair (`BTCUSDT`) and translate to
each venue:

| Venue | Pair | Translation |
|---|---|---|
| Binance | `BTCUSDT` | identity |
| Bybit   | `BTCUSDT` | identity |
| OKX     | `BTC-USDT-SWAP` | `_okx_inst(symbol)` splits on USDT/USDC/USD, inserts `-`, appends `-SWAP` |

A venue that returns empty / 404 is silently dropped from the response (no error). Check `venues_count` to see how many succeeded.

## Funding rate semantics

- **Binance `lastFundingRate`**: most recent applied rate. Funding settles every 8h at 00/08/16 UTC.
- **Bybit `fundingRate`**: same cadence, sometimes 4h on alt pairs.
- **OKX `fundingRate`**: predicted next-period rate (not the realized rate). Slightly different from Binance/Bybit semantically.
- `funding_rate_mean` is a simple mean across available venues — useful as a quick "is the market paying longs or shorts on average?" gauge, but **not** a strict cross-venue carry estimate.

## Open interest units

| Venue | Field unit |
|---|---|
| Binance | base coin (e.g. BTC for BTCUSDT) |
| Bybit   | base coin |
| OKX     | contracts; `oi_ccy` is base coin, `oi_usd` is notional USD |

`oi_contracts_sum` is the **raw sum** — meaningful only when units agree (which they roughly do for BTCUSDT across Binance+Bybit; OKX returns contract count and the script keeps it as `oi_contracts` for parity, so the sum is approximate). For precise cross-venue OI, use `oi_usd` from OKX when present.

## Long/short ratios (Binance)

Four series exposed:

- **`global_accounts`** — ratio across all retail accounts (most accounts long? long-skewed crowd).
- **`top_traders_accounts`** — same ratio limited to top-20% PnL accounts (smart money).
- **`top_traders_positions`** — same, but weighted by position size, not account count.
- **`taker_buy_sell`** — ratio of taker-buy volume to taker-sell volume in the period (`ratio = buy/sell`).

Interpretation:
- Global > 1.0 means more accounts long than short. Persistent extremes (>2.5 or <0.6) often precede squeezes.
- When global ratio diverges from top traders' positions (e.g. retail long, top traders short), that's a contrarian signal.
- Taker ratio > 1 = buying pressure dominant.

## Liquidations

Public liquidation feeds have disappeared:
- Binance `allForceOrders` returned `{"code":400,"msg":"The endpoint has been out of maintenance"}` as of 2026.
- Binance `forceOrders` requires auth.
- Bybit / OKX no longer expose liquidations publicly.

Coinglass aggregates liquidations but requires a paid key. If you really need them, use Bitget's MCP or sign up for Coinglass.
