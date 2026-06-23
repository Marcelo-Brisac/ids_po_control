---
name: crypto-markets
description: >
  Crypto market-data lookups. Use when the user wants: (1) a spot quote
  or kline for any Binance pair, (2) market overview (top-N by market
  cap, BTC dominance, fear-greed), (3) perpetual funding, open interest,
  or long/short ratios across major exchanges, (4) BTC on-chain stats
  (hashrate, mempool, difficulty), (5) DeFi TVL, top protocols, yield
  pools, fees, or stablecoin supply, (6) DEX pair lookup, token search,
  or on-chain contract metadata (tax/honeypot signals), or (7) crypto
  news headlines.
---

# Crypto Markets

Five scripts. Hot paths (spot, derivatives, on-chain, dex) are stdlib-only.
News uses `feedparser` (lazy-imported — install only if you need it).

| Script | Deps | Covers |
|---|---|---|
| `scripts/spot.py`        | stdlib       | Binance quote/klines + CoinGecko top-N/global/trending + alternative.me fear-greed |
| `scripts/derivatives.py` | stdlib       | funding / OI / long-short ratio across Binance / Bybit / OKX |
| `scripts/onchain.py`     | stdlib       | BTC network stats (blockchain.info + blockchair), DefiLlama TVL / protocols / **yield pools / fees** / stablecoins |
| `scripts/dex.py`         | stdlib       | DEX pairs / token search / contract lookup / trending across 80+ chains (DexScreener primary, GeckoTerminal fallback) |
| `scripts/news.py`        | `feedparser` | CoinDesk / CoinTelegraph / Decrypt / BitcoinMagazine / TheBlock RSS aggregation |

Install for news (other scripts run without it):

```bash
# At the skill root (where pyproject.toml lives)
uv sync                          # preferred — creates .venv with all deps pinned
# or:
pip install 'feedparser>=6.0,<7'
```

`news.py` emits `{"error":"feedparser not installed","install":"..."}` if missing.

## CLI

### spot.py (stdlib)

```bash
./scripts/spot.py quote SYM[,SYM,...]         # 24hr ticker; Binance pairs (BTCUSDT,...)
./scripts/spot.py klines SYM --interval 1h --limit 200
./scripts/spot.py top --limit 20 --vs usd     # top N by market cap (CoinGecko)
./scripts/spot.py global                      # total mcap + BTC/ETH dominance
./scripts/spot.py trending --limit 15         # search-trending coins (24h)
./scripts/spot.py fear-greed --limit 30       # alternative.me Fear & Greed series
```

Intervals: `1m 3m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 3d 1w 1M`.
Pairs: any Binance spot pair (USDT/USDC/USD/BTC/ETH/BUSD quote).

→ CoinGecko field semantics, ATH/ATL caveats, vs-currency list: [references/spot.md](references/spot.md)

### derivatives.py (stdlib)

```bash
./scripts/derivatives.py funding SYM                       # current funding across Binance+Bybit+OKX (with mean)
./scripts/derivatives.py funding-history SYM --venue binance --limit 30
./scripts/derivatives.py oi SYM                            # open interest snapshot across venues
./scripts/derivatives.py lsr SYM --period 1h --limit 30    # long/short ratios (global, top traders, taker)
```

Symbols are Binance-style (`BTCUSDT`). OKX swap symbol (`BTC-USDT-SWAP`) is derived automatically. A venue that doesn't list the pair is silently dropped from the response.

LSR periods: `5m 15m 30m 1h 2h 4h 6h 12h 1d`.

→ Funding-rate-mean caveats, OI-units across venues, LSR interpretation: [references/derivatives.md](references/derivatives.md)

### onchain.py (stdlib)

```bash
./scripts/onchain.py btc-stats                  # blockchain.info snapshot
./scripts/onchain.py btc-chair                  # Blockchair snapshot (different fields)
./scripts/onchain.py tvl                        # total DeFi TVL + 24h/7d/30d change
./scripts/onchain.py tvl-chains --limit 20      # TVL per chain (top N)
./scripts/onchain.py protocols --limit 20       # top DeFi protocols by TVL
./scripts/onchain.py pools --limit 20 --sort apy --stablecoin-only --min-tvl 1e8
                                                # DeFi yield pools (filter by chain/project/symbol)
./scripts/onchain.py fees --metric revenue --window 7d --limit 20
                                                # protocols ranked by fees or revenue
./scripts/onchain.py stablecoins --limit 15     # top stablecoins by supply
./scripts/onchain.py stablecoin-total           # aggregate stablecoin supply + change
```

→ BTC stat field meanings, DefiLlama categories, pool / fees schema, stablecoin peg types: [references/onchain.md](references/onchain.md)

### dex.py (stdlib)

```bash
./scripts/dex.py search "PEPE"                       # pairs by token name/symbol/address; auto-sorted by liquidity
./scripts/dex.py contract 0x51ba...f6 --chain bsc    # all DEX pairs for a token contract (tax/honeypot heuristics)
./scripts/dex.py pair bsc 0x...                      # one specific pair by chain + pair address
./scripts/dex.py trending --chain solana --limit 15  # trending pools (DexScreener boosts → GT trending fallback)
./scripts/dex.py trending --source geckoterminal     # GT volume-based trending only
./scripts/dex.py networks                            # supported chain id mapping
```

Chains: `ethereum bsc solana polygon arbitrum base optimism avalanche fantom linea blast sui ton tron cronos celo` (pass-through if not in the map). DexScreener returns flat pair dicts (price, liquidity, volume, txn counts, price-change asymmetry, FDV, market cap, socials). GeckoTerminal is the fallback for the same shape.

→ Tax/honeypot heuristic interpretation, provider differences, chain naming: [references/dex.md](references/dex.md)

### news.py (feedparser)

```bash
./scripts/news.py feeds                        # list available feed names (no install)
./scripts/news.py latest --limit 30            # merged feed, sorted by date desc
./scripts/news.py latest --feeds coindesk,decrypt --limit 20
./scripts/news.py feed coindesk --limit 20     # one feed
./scripts/news.py search "ETF" --limit 20      # substring search across recent items
```

Feeds: `coindesk cointelegraph decrypt bitcoinmagazine theblock`.

→ Feed cadence, item field semantics, adding new feeds: [references/news.md](references/news.md)

## Source strategy

| Need | Primary | Fallback |
|---|---|---|
| Spot quote / klines | Binance `api/v3` | — |
| Top-N / global mcap / dominance | CoinGecko free | — (CMC needs key) |
| Fear & Greed | alternative.me | — |
| Funding / OI | Binance fapi + Bybit v5 + OKX v5 | — (venues fall back to each other) |
| Long/short ratio | Binance `futures/data` | — (Bybit/OKX don't expose this publicly) |
| BTC network stats | blockchain.info | Blockchair (different metrics) |
| DeFi TVL / protocols / pools / fees | DefiLlama (`api.llama.fi` + `yields.llama.fi`) | — (best free source) |
| Stablecoins | DefiLlama `stablecoins.llama.fi` | — |
| DEX pairs / token contract / trending | DexScreener `api.dexscreener.com` | GeckoTerminal `api.geckoterminal.com` |
| News | RSS direct (no aggregator) | — (CryptoPanic/CMC/Bitget all keyed) |

→ Endpoint catalogue + evaluated alternatives: [references/sources.md](references/sources.md)

## Rate limits

CoinGecko free tier throttles ~10-30 req/min by IP; Binance/Bybit/OKX
public endpoints are generous but rate-limited per IP; DefiLlama is
relaxed but slow on the big payloads. On failure, **don't retry** —
return the error and move on.
