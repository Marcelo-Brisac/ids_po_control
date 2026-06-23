# spot.py — reference

Binance spot + CoinGecko free + alternative.me Fear & Greed.

## Endpoints

```
GET https://api.binance.com/api/v3/ticker/24hr?symbols=["BTCUSDT","ETHUSDT"]
GET https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=200
GET https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=20
GET https://api.coingecko.com/api/v3/global
GET https://api.coingecko.com/api/v3/search/trending
GET https://api.alternative.me/fng/?limit=30
```

## Symbol conventions

- Binance pairs: BASE+QUOTE, no separator, uppercase. Common quotes: USDT, USDC, BTC, ETH, BUSD (deprecated but some pairs still listed), FDUSD.
- CoinGecko uses lowercase string ids ("bitcoin", "ethereum"). The `top` / `trending` commands return both id and uppercase symbol.

## Caveats

- **Klines timestamps are ms** (Binance convention). 1d klines close at 00:00 UTC.
- **CoinGecko `pct_1h/7d` requires extra params** — already wired via `price_change_percentage` defaults in the script. If you see `None`, the field wasn't returned for that asset.
- **CoinGecko rate-limit** on free tier is ~10-30 req/min by IP. Subsequent calls 429 — script returns `{"error":"http 429:..."}`.
- **Fear & Greed updates daily** at ~00:00 UTC. `time_until_update` is in seconds, only on the latest item.
- **Trending limit** — CoinGecko returns ~15 coins regardless; `--limit` truncates.

## CoinGecko vs Binance

CoinGecko prices are aggregated cross-venue (volume-weighted); Binance is venue-specific. For "what is BTC worth right now in deep liquidity", use Binance `quote BTCUSDT`. For "what is XYZ-no-binance-listing worth", use `top` and look up the coin.
