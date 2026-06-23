# onchain.py — reference

BTC network stats + DeFi TVL + DeFi yield pools + protocol fees/revenue + stablecoin supply. Keyless.

## Endpoints

```
GET https://blockchain.info/stats?format=json
GET https://api.blockchair.com/bitcoin/stats
GET https://api.llama.fi/v2/historicalChainTvl
GET https://api.llama.fi/v2/chains
GET https://api.llama.fi/protocols
GET https://api.llama.fi/overview/fees?dataType=dailyFees|dailyRevenue
GET https://yields.llama.fi/pools
GET https://stablecoins.llama.fi/stablecoins?includePrices=false
GET https://stablecoins.llama.fi/stablecoincharts/all
```

## DeFi yield pools (`pools`)

`yields.llama.fi/pools` returns one row per pool across every protocol DefiLlama tracks (~20k rows, 1-2s, 13MB). Each row carries:

| Field | Meaning |
|---|---|
| `apy` | total APY (base + reward) |
| `apyBase` | yield from organic protocol activity (e.g. lending interest) |
| `apyReward` | yield paid in protocol's reward token (often inflationary) |
| `apyPct1D / 7D / 30D` | absolute change in APY over the window — note **percentage points**, not percent change |
| `apyMean30d` | smoothed 30-day mean APY |
| `tvlUsd` | pool TVL |
| `stablecoin` | true if both legs are stables |
| `ilRisk` | `no` / `yes` — DefiLlama's IL classification |
| `exposure` | `single` / `multi` — number of distinct assets |
| `outlier` | true if DefiLlama suspects bad data |
| `predictions` | ML model output: `Stable/Up`, `Stable/Down`, `Trending/Up`, `Trending/Down` + confidence |

**Filter ergonomics**: `--chain Ethereum`, `--project aave-v3`, `--symbol USDC` (substring), `--stablecoin-only`, `--min-tvl 1e8`. Combine with `--sort apy|tvl`.

Watch-outs:
- A pool can show 100%+ APY purely from `apyReward` (unsustainable). Cross-check `apyBase` for the durable yield.
- `outlier=true` rows survive the API but are usually wrong — skip them unless explicitly investigating.
- `apyPct1D` of `7.0` means **APY moved by 7 percentage points** in 24h — for a 5% APY pool, that's a 140% jump.

## Protocol fees & revenue (`fees`)

`api.llama.fi/overview/fees` returns one row per protocol that DefiLlama has a fee adapter for (~2k rows). Two modes:

- `--metric fees` (default, `dataType=dailyFees`): total user-paid fees flowing through the protocol.
- `--metric revenue` (`dataType=dailyRevenue`): protocol-retained share.

`fees - revenue ≈ what flows to LPs / depositors / token holders`. For Tether / Circle the difference is interest income on backing assets vs distributions, both rolled into one number — read each row's `category` for context (Stablecoin Issuer, DEX, Lending, CDP, Derivatives, Chain, ...).

Windows: `24h | 7d | 30d` via `--window`. Sort is by the selected window descending.

`total_all_protocols_*` in the response is the aggregate across the whole list, useful as a denominator for share-of-market computations.

## BTC stats — blockchain.info vs Blockchair

Both give a "BTC network now" snapshot but expose different fields. Use both for completeness — `blockchain.info` for activity (tx counts, miner revenue, recent volume); `Blockchair` for mempool + fee detail.

| Metric | blockchain.info | Blockchair |
|---|---|---|
| Block height | ✓ | ✓ |
| Hashrate (GH/s) | ✓ | ✓ (`hashrate_24h`) |
| Difficulty | ✓ | ✓ + `next_difficulty_estimate` |
| Mempool tx count | — | ✓ |
| Mempool size (bytes) | — | ✓ |
| Mempool total fee USD | — | ✓ |
| Tx count 24h | ✓ | ✓ |
| Miner revenue (BTC + USD) | ✓ | — |
| 24h trade/tx volume | ✓ | — |
| Mean/median tx fee | — | ✓ |
| Market cap | — | ✓ |
| BTC dominance | — | ✓ |

Mempool size doesn't always correlate with congestion — a thin mempool with high-fee txs can still be congested.

## DefiLlama TVL

- **`tvl`**: aggregate across all chains. Returns latest snapshot + 24h/7d/30d changes (script computes these from the historical chart).
- **`tvl-chains`**: per-chain TVL, sorted desc. Top chains are typically Ethereum, Tron, Solana, BSC, Bitcoin (via L2/BRC20), Base, Arbitrum.
- **`protocols`**: per-protocol TVL with 24h/7d % change. `category` is the strategy bucket (Lending, DEX, Liquid Staking, CDP, ...).

DefiLlama numbers can revise retroactively when new pools are catalogued — don't treat historical TVL as fully immutable.

## Stablecoins

- **`stablecoins`**: top N by circulating supply (USDT, USDC, DAI, FDUSD, ...). Supply prev day/week/month included for change computation.
- **`stablecoin-total`**: aggregate supply across all stables. Strong proxy for "dry powder" entering or leaving crypto.

Peg types: `peggedUSD`, `peggedEUR`, `peggedVAR` (variable), `peggedCNY`, etc. Mechanism: `fiat-backed`, `crypto-backed`, `algorithmic`, `hybrid`.

`/stablecoins` endpoint returns ~500 KB. For just totals, use `stablecoin-total` (smaller chart payload).
