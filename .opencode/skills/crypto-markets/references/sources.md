# Sources catalogue — crypto-markets

Raw endpoint reference. Verified 2026-05-28. All keyless.

## Binance (spot + futures)

```
# Spot
GET https://api.binance.com/api/v3/ticker/24hr?symbols=["BTCUSDT","ETHUSDT"]
GET https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=500

# Futures (linear USDT-margined perpetuals)
GET https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT
GET https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=30
GET https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT
GET https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol=BTCUSDT&period=1h&limit=30
GET https://fapi.binance.com/futures/data/topLongShortAccountRatio?...
GET https://fapi.binance.com/futures/data/topLongShortPositionRatio?...
GET https://fapi.binance.com/futures/data/takerlongshortRatio?...
```

Rate limit: 1200 weight/minute per IP for spot; ~2400 weight/minute for fapi. Most endpoints cost 1 weight.

## Bybit v5

```
GET https://api.bybit.com/v5/market/tickers?category=linear&symbol=BTCUSDT
GET https://api.bybit.com/v5/market/funding/history?category=linear&symbol=BTCUSDT&limit=30
GET https://api.bybit.com/v5/market/open-interest?category=linear&symbol=BTCUSDT&intervalTime=5min&limit=1
```

`category` ∈ {spot, linear, inverse, option}. Use `linear` for USDT-margined perpetuals.

## OKX v5

```
GET https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP
GET https://www.okx.com/api/v5/public/funding-rate-history?instId=BTC-USDT-SWAP&limit=30
GET https://www.okx.com/api/v5/public/open-interest?instType=SWAP&instId=BTC-USDT-SWAP
```

`instType` ∈ {SPOT, MARGIN, SWAP, FUTURES, OPTION}. Swap = perpetual.

## CoinGecko free

```
GET https://api.coingecko.com/api/v3/global
GET https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=20
GET https://api.coingecko.com/api/v3/search/trending
```

Free tier: ~10-30 req/min per IP. Demo Plan adds a soft limit of 30 req/min with key. `https://pro-api.coingecko.com` requires paid key.

## alternative.me

```
GET https://api.alternative.me/fng/?limit=30
```

Updates daily ~00:00 UTC. Returns score 0-100 + classification (Extreme Fear / Fear / Neutral / Greed / Extreme Greed).

## blockchain.info

```
GET https://blockchain.info/stats?format=json
GET https://blockchain.info/q/getdifficulty       # plaintext
```

Generous rate limit; long-stable JSON shape.

## Blockchair

```
GET https://api.blockchair.com/bitcoin/stats
GET https://api.blockchair.com/ethereum/stats     # also available
```

Free tier: 1440 req/day per IP without key. Supports 17+ chains.

## DefiLlama

```
GET https://api.llama.fi/v2/historicalChainTvl
GET https://api.llama.fi/v2/chains
GET https://api.llama.fi/protocols                # ~8MB payload
GET https://api.llama.fi/overview/fees?dataType=dailyFees       # ~3MB
GET https://api.llama.fi/overview/fees?dataType=dailyRevenue
GET https://yields.llama.fi/pools                 # ~13MB, ~20k pools
GET https://stablecoins.llama.fi/stablecoins?includePrices=false  # ~500KB
GET https://stablecoins.llama.fi/stablecoincharts/all
```

No rate limit advertised, but `/protocols` and `/pools` are slow (~3-15s) due to payload size. Single source of truth for DeFi TVL, yield pool APYs, and protocol fees/revenue.

## DexScreener

```
GET https://api.dexscreener.com/latest/dex/search?q=PEPE
GET https://api.dexscreener.com/latest/dex/tokens/{address}     # cross-chain
GET https://api.dexscreener.com/latest/dex/pairs/{chain}/{pair_address}
GET https://api.dexscreener.com/token-boosts/latest/v1
```

No key. ~300 req/min/IP observed. Covers 80+ chains, 300+ DEXs, 2M+ tokens.

## GeckoTerminal

```
GET https://api.geckoterminal.com/api/v2/search/pools?query=PEPE
GET https://api.geckoterminal.com/api/v2/networks/{net}/tokens/{addr}/pools
GET https://api.geckoterminal.com/api/v2/networks/{net}/pools/{pair_address}
GET https://api.geckoterminal.com/api/v2/networks/{net}/trending_pools
GET https://api.geckoterminal.com/api/v2/networks/trending_pools
```

CoinGecko's on-chain product. No key. ~30 req/min/IP (tight). JSON:API shape. Used as fallback to DexScreener — same surface, normalized to the same flat shape.

## RSS feeds

See `references/news.md` for the list. All are HTTP polls; no API.

## Evaluated alternatives

| Source | Verdict |
|---|---|
| CoinMarketCap API | Requires `X-CMC_PRO_API_KEY`. Free tier exists but limited. CoinGecko covers same ground keylessly. |
| Glassnode | All endpoints require key + tier subscription. |
| CryptoQuant | Same — keyed. |
| Messari | Keyed. |
| CryptoCompare | Free tier requires sign-up + key. |
| DEXTools | API requires key on free tier. DexScreener + GeckoTerminal cover the same surface keylessly. |
| Birdeye | Free tier requires sign-up + API key. |
| Moralis | Same. |
| GoPlus Security API | Excellent honeypot/tax detection but requires API key (rate-limited even with key). Candidate for paid add-on. |
| Honeypot.is | Public API, BSC-only, rate-limited per IP. Candidate for third fallback specifically for BSC token checks. |
| Token Sniffer | HTML scrape only; very fragile, Cloudflare-protected. |
| Farside (ETF flows) | HTML scrape only, fragile. Cloudflare-protected. |
| SoSoValue (ETF flows) | API exists but undocumented; needs reverse-engineering + may key. |
| mempool.space | Excellent BTC mempool API but blocked from our sandbox egress. Use blockchain.info / Blockchair instead. |
| CryptoPanic | `/free/v1/` 404 without auth on current free tier. RSS direct works (`coindesk`, etc.). |
| Bitget News API | `news.bitget.com` requires sign-up. RSS aggregation covers same ground. |
| Coincap | Works, but CoinGecko has richer fields for the same routes. |
