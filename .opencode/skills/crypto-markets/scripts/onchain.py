#!/usr/bin/env python3
"""crypto-markets / onchain: BTC/ETH network stats, DeFi TVL, yield pools,
protocol fees/revenue, stablecoin supply. Keyless. Stdlib only. Providers:

  - blockchain.info / blockchair         — BTC network stats (hashrate, mempool, difficulty)
  - api.llama.fi                         — DeFi TVL + protocols + fees/revenue
  - yields.llama.fi                      — DeFi yield pools (APY rankings)
  - stablecoins.llama.fi                 — Stablecoin supply

Output: JSON to stdout. Errors: JSON {"error": "..."} with exit code 1.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, NoReturn

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
TIMEOUT = 15

BC_INFO = "https://blockchain.info"
BLOCKCHAIR = "https://api.blockchair.com"
LLAMA = "https://api.llama.fi"
YIELDS = "https://yields.llama.fi"
STABLES = "https://stablecoins.llama.fi"


def die(msg: str, code: int = 1) -> NoReturn:
    print(json.dumps({"error": msg}, ensure_ascii=False))
    sys.exit(code)


def _get_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def cmd_btc_stats(args):
    """BTC network snapshot: hashrate, difficulty, mining, recent activity."""
    s = _get_json(f"{BC_INFO}/stats?format=json")
    return {
        "block_height": s.get("n_blocks_total"),
        "hashrate_ghs": s.get("hash_rate"),
        "difficulty": s.get("difficulty"),
        "minutes_between_blocks": s.get("minutes_between_blocks"),
        "n_tx_24h": s.get("n_tx"),
        "n_blocks_mined_24h": s.get("n_blocks_mined"),
        "blocks_size_bytes": s.get("blocks_size"),
        "miners_revenue_btc": (s.get("miners_revenue_btc") or 0) / 1e8 if s.get("miners_revenue_btc") else None,
        "miners_revenue_usd": s.get("miners_revenue_usd"),
        "total_fees_btc": (s.get("total_fees_btc") or 0) / 1e8 if s.get("total_fees_btc") else None,
        "market_price_usd": s.get("market_price_usd"),
        "circulating_btc": (s.get("totalbc") or 0) / 1e8 if s.get("totalbc") else None,
        "estimated_btc_sent_24h": (s.get("estimated_btc_sent") or 0) / 1e8 if s.get("estimated_btc_sent") else None,
        "estimated_tx_volume_usd_24h": s.get("estimated_transaction_volume_usd"),
        "trade_volume_btc_24h": s.get("trade_volume_btc"),
        "trade_volume_usd_24h": s.get("trade_volume_usd"),
        "next_retarget": s.get("nextretarget"),
        "timestamp": int((s.get("timestamp") or 0) / 1000) if s.get("timestamp") else None,
        "source": "blockchain.info",
    }


def cmd_btc_chair(args):
    """Same BTC snapshot via Blockchair (different metric set: outputs, fee_per_kb, etc.)."""
    j = _get_json(f"{BLOCKCHAIR}/bitcoin/stats")
    d = j.get("data") or {}
    return {
        "blocks": d.get("blocks"),
        "transactions": d.get("transactions"),
        "circulating_supply": d.get("circulation"),
        "mempool_tx": d.get("mempool_transactions"),
        "mempool_size_bytes": d.get("mempool_size"),
        "mempool_total_fee_usd": d.get("mempool_total_fee_usd"),
        "hashrate_24h": d.get("hashrate_24h"),
        "difficulty": d.get("difficulty"),
        "next_difficulty_estimate": d.get("next_difficulty_estimate"),
        "best_block_time": d.get("best_block_time"),
        "average_fee_btc": (d.get("average_transaction_fee_24h") or 0) / 1e8 if d.get("average_transaction_fee_24h") else None,
        "median_fee_btc": (d.get("median_transaction_fee_24h") or 0) / 1e8 if d.get("median_transaction_fee_24h") else None,
        "market_price_usd": d.get("market_price_usd"),
        "market_cap_usd": d.get("market_cap_usd"),
        "market_dominance_pct": d.get("market_dominance_percentage"),
        "source": "blockchair",
    }


def cmd_tvl(args):
    """Total DeFi TVL across all chains (single number)."""
    j = _get_json(f"{LLAMA}/v2/historicalChainTvl")
    rows = j or []
    if not rows:
        return {"error": "no TVL data"}
    rows.sort(key=lambda r: r["date"])
    latest = rows[-1]
    prev_day = next((r for r in reversed(rows[:-1]) if r["date"] <= latest["date"] - 86400), None)
    prev_week = next((r for r in reversed(rows[:-1]) if r["date"] <= latest["date"] - 7 * 86400), None)
    prev_month = next((r for r in reversed(rows[:-1]) if r["date"] <= latest["date"] - 30 * 86400), None)

    def pct(a, b):
        return ((a - b) / b * 100) if b else None

    return {
        "tvl_usd": latest["tvl"],
        "timestamp": latest["date"],
        "tvl_prev_day": prev_day["tvl"] if prev_day else None,
        "tvl_prev_week": prev_week["tvl"] if prev_week else None,
        "tvl_prev_month": prev_month["tvl"] if prev_month else None,
        "pct_24h": pct(latest["tvl"], prev_day["tvl"]) if prev_day else None,
        "pct_7d": pct(latest["tvl"], prev_week["tvl"]) if prev_week else None,
        "pct_30d": pct(latest["tvl"], prev_month["tvl"]) if prev_month else None,
        "source": "defillama",
    }


def cmd_tvl_chains(args):
    """TVL per chain (top N)."""
    j = _get_json(f"{LLAMA}/v2/chains")
    rows = j or []
    rows.sort(key=lambda r: r.get("tvl") or 0, reverse=True)
    return [
        {
            "name": r.get("name"),
            "tvl_usd": r.get("tvl"),
            "token_symbol": r.get("tokenSymbol"),
            "gecko_id": r.get("gecko_id"),
        }
        for r in rows[: args.limit]
    ]


def cmd_protocols(args):
    """Top DeFi protocols by TVL."""
    j = _get_json(f"{LLAMA}/protocols")
    rows = j or []
    rows.sort(key=lambda r: r.get("tvl") or 0, reverse=True)
    return [
        {
            "name": r.get("name"),
            "category": r.get("category"),
            "chain": r.get("chain"),
            "chains": r.get("chains"),
            "tvl_usd": r.get("tvl"),
            "pct_24h": r.get("change_1d"),
            "pct_7d": r.get("change_7d"),
            "mcap_usd": r.get("mcap"),
            "symbol": r.get("symbol"),
        }
        for r in rows[: args.limit]
    ]


def cmd_stablecoins(args):
    """Top stablecoins by circulating supply."""
    j = _get_json(f"{STABLES}/stablecoins?includePrices=false")
    rows = (j or {}).get("peggedAssets") or []
    def _supply(r):
        c = (r.get("circulating") or {})
        return c.get("peggedUSD") or 0
    rows.sort(key=_supply, reverse=True)
    out = []
    for r in rows[: args.limit]:
        c = r.get("circulating") or {}
        pd = r.get("circulatingPrevDay") or {}
        pw = r.get("circulatingPrevWeek") or {}
        pm = r.get("circulatingPrevMonth") or {}
        sup = c.get("peggedUSD")
        out.append({
            "symbol": r.get("symbol"),
            "name": r.get("name"),
            "supply_usd": sup,
            "supply_prev_day": pd.get("peggedUSD"),
            "supply_prev_week": pw.get("peggedUSD"),
            "supply_prev_month": pm.get("peggedUSD"),
            "peg_type": r.get("pegType"),
            "peg_mechanism": r.get("pegMechanism"),
            "gecko_id": r.get("gecko_id"),
        })
    return out


def cmd_pools(args):
    """DeFi yield pools — top N sorted by APY or TVL, with optional filters.

    Filters: --chain (e.g. Ethereum), --project (e.g. aave-v3), --symbol substring,
    --stablecoin-only, --min-tvl USD floor.
    Sort: --sort apy|tvl (default apy).
    """
    j = _get_json(f"{YIELDS}/pools")
    rows = (j or {}).get("data") or []
    chain = (args.chain or "").lower() or None
    project = (args.project or "").lower() or None
    sym = (args.symbol or "").upper() or None
    min_tvl = args.min_tvl
    stable_only = args.stablecoin_only

    def keep(r):
        if chain and (r.get("chain") or "").lower() != chain:
            return False
        if project and (r.get("project") or "").lower() != project:
            return False
        if sym and sym not in (r.get("symbol") or "").upper():
            return False
        if stable_only and not r.get("stablecoin"):
            return False
        if min_tvl is not None and (r.get("tvlUsd") or 0) < min_tvl:
            return False
        return True

    rows = [r for r in rows if keep(r)]
    key = (lambda r: r.get("tvlUsd") or 0) if args.sort == "tvl" else (lambda r: r.get("apy") or 0)
    rows.sort(key=key, reverse=True)
    return [
        {
            "chain": r.get("chain"),
            "project": r.get("project"),
            "symbol": r.get("symbol"),
            "pool_meta": r.get("poolMeta"),
            "tvl_usd": r.get("tvlUsd"),
            "apy": r.get("apy"),
            "apy_base": r.get("apyBase"),
            "apy_reward": r.get("apyReward"),
            "apy_pct_1d": r.get("apyPct1D"),
            "apy_pct_7d": r.get("apyPct7D"),
            "apy_pct_30d": r.get("apyPct30D"),
            "apy_mean_30d": r.get("apyMean30d"),
            "stablecoin": r.get("stablecoin"),
            "il_risk": r.get("ilRisk"),
            "exposure": r.get("exposure"),
            "reward_tokens": r.get("rewardTokens"),
            "outlier": r.get("outlier"),
            "pool_id": r.get("pool"),
            "source": "defillama_yields",
        }
        for r in rows[: args.limit]
    ]


def cmd_fees(args):
    """Top protocols by fees (24h default) or revenue. DefiLlama /overview/fees.

    --metric fees|revenue (default fees)
    --window 24h|7d|30d   (default 24h)
    """
    dtype = "dailyRevenue" if args.metric == "revenue" else "dailyFees"
    qs = urllib.parse.urlencode({
        "excludeTotalDataChart": "true",
        "excludeTotalDataChartBreakdown": "true",
        "dataType": dtype,
    })
    j = _get_json(f"{LLAMA}/overview/fees?{qs}")
    rows = (j or {}).get("protocols") or []

    win_key = {"24h": "total24h", "7d": "total7d", "30d": "total30d"}[args.window]
    rows.sort(key=lambda r: r.get(win_key) or 0, reverse=True)

    return {
        "metric": args.metric,
        "window": args.window,
        "total_all_protocols_24h": (j or {}).get("total24h"),
        "total_all_protocols_7d": (j or {}).get("total7d"),
        "total_all_protocols_30d": (j or {}).get("total30d"),
        "change_1d_pct": (j or {}).get("change_1d"),
        "change_7d_pct": (j or {}).get("change_7d"),
        "change_1m_pct": (j or {}).get("change_1m"),
        "protocols": [
            {
                "name": r.get("name") or r.get("displayName"),
                "category": r.get("category"),
                "chains": r.get("chains"),
                "total_24h": r.get("total24h"),
                "total_7d": r.get("total7d"),
                "total_30d": r.get("total30d"),
                "change_1d_pct": r.get("change_1d"),
                "change_7d_pct": r.get("change_7d"),
                "change_1m_pct": r.get("change_1m"),
                "slug": r.get("slug"),
            }
            for r in rows[: args.limit]
        ],
        "source": "defillama_fees",
    }


def cmd_stablecoin_total(args):
    """Aggregate stablecoin market cap + change."""
    j = _get_json(f"{STABLES}/stablecoincharts/all")
    rows = j or []
    if not rows:
        return {"error": "no stablecoin chart data"}
    rows.sort(key=lambda r: int(r["date"]))
    def total(r):
        return (r.get("totalCirculatingUSD") or {}).get("peggedUSD") or 0
    latest = rows[-1]
    prev_day = next((r for r in reversed(rows[:-1]) if int(r["date"]) <= int(latest["date"]) - 86400), None)
    prev_week = next((r for r in reversed(rows[:-1]) if int(r["date"]) <= int(latest["date"]) - 7 * 86400), None)
    prev_month = next((r for r in reversed(rows[:-1]) if int(r["date"]) <= int(latest["date"]) - 30 * 86400), None)

    def pct(a, b):
        return ((a - b) / b * 100) if b else None

    cur, p1, p7, p30 = total(latest), total(prev_day) if prev_day else None, total(prev_week) if prev_week else None, total(prev_month) if prev_month else None
    return {
        "supply_usd": cur,
        "timestamp": int(latest["date"]),
        "supply_prev_day": p1,
        "supply_prev_week": p7,
        "supply_prev_month": p30,
        "pct_24h": pct(cur, p1) if p1 else None,
        "pct_7d": pct(cur, p7) if p7 else None,
        "pct_30d": pct(cur, p30) if p30 else None,
        "source": "defillama_stablecoins",
    }


def main() -> None:
    p = argparse.ArgumentParser(prog="onchain.py", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("btc-stats", help="BTC network snapshot (blockchain.info)").set_defaults(func=cmd_btc_stats)
    sub.add_parser("btc-chair", help="BTC stats from Blockchair (different metrics)").set_defaults(func=cmd_btc_chair)
    sub.add_parser("tvl", help="total DeFi TVL across all chains + change").set_defaults(func=cmd_tvl)

    pc = sub.add_parser("tvl-chains", help="TVL per chain (top N)")
    pc.add_argument("--limit", type=int, default=20)
    pc.set_defaults(func=cmd_tvl_chains)

    pp = sub.add_parser("protocols", help="top DeFi protocols by TVL")
    pp.add_argument("--limit", type=int, default=20)
    pp.set_defaults(func=cmd_protocols)

    py = sub.add_parser("pools", help="DeFi yield pools (top N sorted by APY or TVL)")
    py.add_argument("--limit", type=int, default=20)
    py.add_argument("--chain", default="", help="filter exact chain name (e.g. Ethereum)")
    py.add_argument("--project", default="", help="filter exact project slug (e.g. aave-v3)")
    py.add_argument("--symbol", default="", help="substring match in pool symbol")
    py.add_argument("--stablecoin-only", action="store_true")
    py.add_argument("--min-tvl", type=float, default=None, help="USD floor on TVL")
    py.add_argument("--sort", choices=("apy", "tvl"), default="apy")
    py.set_defaults(func=cmd_pools)

    pf = sub.add_parser("fees", help="protocols ranked by fees or revenue")
    pf.add_argument("--limit", type=int, default=20)
    pf.add_argument("--metric", choices=("fees", "revenue"), default="fees")
    pf.add_argument("--window", choices=("24h", "7d", "30d"), default="24h")
    pf.set_defaults(func=cmd_fees)

    ps = sub.add_parser("stablecoins", help="top stablecoins by supply")
    ps.add_argument("--limit", type=int, default=15)
    ps.set_defaults(func=cmd_stablecoins)

    sub.add_parser("stablecoin-total", help="aggregate stablecoin market cap + change").set_defaults(func=cmd_stablecoin_total)

    args = p.parse_args()
    try:
        out = args.func(args)
    except urllib.error.HTTPError as e:
        die(f"http {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        die(f"network: {e.reason}")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
