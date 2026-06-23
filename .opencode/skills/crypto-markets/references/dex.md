# dex.py — reference

DEX pair lookup, token search, on-chain contract metadata, and trending pools across 80+ chains. Keyless.

## Providers

- **Primary: DexScreener** — `api.dexscreener.com`. No key, no rate limit advertised (~300 req/min/IP observed). Single endpoint family returns rich pair dicts with txn counts, price-change asymmetry, FDV, market cap, socials/websites for some tokens.
- **Fallback: GeckoTerminal** — `api.geckoterminal.com/api/v2`. No key, ~30 req/min/IP. CoinGecko's on-chain product. JSON:API shape (`data` + `included`); script normalizes to the DexScreener flat shape.

Each public command calls DexScreener first, falls back to GeckoTerminal on HTTP/network/decode error or empty result, and dies only when both fail. Every response carries `provider` and `fallback_used` so callers can attribute.

## Endpoints

```
# DexScreener
GET https://api.dexscreener.com/latest/dex/search?q=PEPE
GET https://api.dexscreener.com/latest/dex/tokens/{address}
GET https://api.dexscreener.com/latest/dex/pairs/{chain}/{pair_address}
GET https://api.dexscreener.com/token-boosts/latest/v1

# GeckoTerminal
GET https://api.geckoterminal.com/api/v2/search/pools?query=PEPE
GET https://api.geckoterminal.com/api/v2/networks/{net}/tokens/{address}/pools
GET https://api.geckoterminal.com/api/v2/networks/{net}/pools/{pair_address}
GET https://api.geckoterminal.com/api/v2/networks/{net}/trending_pools
GET https://api.geckoterminal.com/api/v2/networks/trending_pools
```

## Chain id mapping

DexScreener uses long names; GeckoTerminal uses short slugs. Built-in map:

| DexScreener | GeckoTerminal |
|---|---|
| `ethereum` | `eth` |
| `bsc` | `bsc` |
| `solana` | `solana` |
| `polygon` | `polygon_pos` |
| `arbitrum` | `arbitrum` |
| `base` | `base` |
| `optimism` | `optimism` |
| `avalanche` | `avax` |
| `fantom` | `ftm` |
| `linea` | `linea` |
| `blast` | `blast` |
| `sui` | `sui` |
| `ton` | `ton` |
| `tron` | `tron` |
| `cronos` | `cro` |
| `celo` | `celo` |

Unknown chain ids pass through unchanged. Callers should pass DexScreener-style names (`ethereum`, `bsc`, ...).

## Tax / honeypot heuristics

**Neither provider tags `honeypot=true`.** Surface the underlying fields and let the caller judge:

| Signal | What to look for |
|---|---|
| Buy/sell tx asymmetry | `txns_h24_buys` vs `txns_h24_sells`. Many buys + zero sells over 24h ≈ honeypot. |
| Price-change asymmetry | `price_change_h1_pct > 0` with no realized 24h volume ≈ phantom price. |
| Liquidity-to-volume mismatch | `volume_h24 >> liquidity_usd` over multiple bars ≈ wash trading. |
| Liquidity locked | DexScreener does NOT expose lock data. Use a separate tool. |
| Tax rate | Neither provider exposes buy/sell tax %. Use a chain-specific simulator (BscScan / Etherscan + token contract source). |

A common pattern for "is this BSC token a honeypot?": run `contract --chain bsc <addr>`, then check the top-liquidity pair's 24h buy/sell counts and the symmetry of `price_change_h1_pct` vs `price_change_h24_pct`. If 24h has 800 buys and 3 sells, that's a strong honeypot signal regardless of the price chart.

## Normalized output shape

Every pair / contract / trending row uses the same dict:

```json
{
  "chain": "bsc",
  "dex": "pancakeswap",
  "pair_address": "0x...",
  "url": "https://dexscreener.com/...",
  "base":  {"address": "0x...", "symbol": "PEPE", "name": "Pepe"},
  "quote": {"address": "0x...", "symbol": "WBNB", "name": "Wrapped BNB"},
  "price_usd": 0.0000012,
  "price_native": 0.0000000045,
  "liquidity_usd": 1234567,
  "liquidity_base": 9.8e11,
  "liquidity_quote": 1234,
  "volume_h24": 5432100,
  "volume_h6": 765432,
  "volume_h1": 87654,
  "price_change_h1_pct": 2.3,
  "price_change_h6_pct": -4.1,
  "price_change_h24_pct": 12.8,
  "txns_h24_buys": 1234,
  "txns_h24_sells": 987,
  "fdv_usd": 50000000,
  "market_cap_usd": 12000000,
  "pair_created_ms": 1700000000000,
  "socials": [{"type": "twitter", "url": "..."}],
  "websites": [{"label": "Website", "url": "..."}],
  "source": "dexscreener"
}
```

GeckoTerminal fills the same fields; `liquidity_base / liquidity_quote / pair_created_ms / socials / websites` may be null because GT doesn't expose them.

## Trending command notes

`dex trending` has two modes:

- `--source auto` (default): DexScreener `token-boosts/latest/v1` first — these are **paid promotion slots**, not volume-based. On empty or error, falls back to GT `trending_pools` which is curated by volume/momentum.
- `--source geckoterminal`: skip DexScreener; go straight to GT trending. Use this when you want real volume-based trending rather than paid boosts.

## Provider-specific quirks

- **DexScreener `tokens/{address}` is cross-chain.** Returns pairs from every chain the address exists on; we filter by `--chain` client-side when set.
- **DexScreener `search/?q=` ranks by an internal score**, not liquidity. Script re-sorts by `liquidity_usd` descending for stability.
- **GeckoTerminal pagination** is 20 per page. Script fetches page 1 only; expand with `&page=` if you need >20.
- **GeckoTerminal rate limit** is the tighter one (~30 req/min). When DexScreener fails for any reason, expect GT to be the bottleneck.
- **Both providers occasionally return `priceUsd` as a string** — the normalizer coerces to float; `None` propagates if missing.

## Evaluated alternatives

| Source | Verdict |
|---|---|
| DEXTools | Requires API key on free tier. |
| 1inch fusion API | Quote API only — no pair / token metadata. |
| Birdeye | Free tier requires sign-up + API key. |
| Moralis Wallet API | Same. |
| GoPlus Security API | Excellent honeypot/tax-rate detection — but **requires API key**, and rate-limit is tight even with key. Worth evaluating as a paid add-on. |
| Token Sniffer | HTML scrape only; very fragile, Cloudflare-protected. |
| Honeypot.is | Public API but BSC-only and rate-limited per IP. Could be wired as a third fallback specifically for BSC token checks if user demand warrants. |
