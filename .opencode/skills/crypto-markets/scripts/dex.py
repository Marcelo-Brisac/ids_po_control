#!/usr/bin/env python3
"""crypto-markets / dex: DEX pairs, token search, and on-chain contract lookup
across 80+ chains and 300+ DEXs. Keyless. Stdlib only. Providers:

  - api.dexscreener.com         — primary (free, no key, fast, broad coverage)
  - api.geckoterminal.com       — fallback (CoinGecko on-chain product, free)

Use cases (driven by user demand):
  - "Look up tax / honeypot info for BSC token 0x...".  → contract --chain bsc 0x...
  - "Find PEPE pairs across DEXs"                       → search PEPE
  - "What's trending on Solana DEXs right now"          → trending --chain solana

Output: JSON to stdout. Errors: JSON {"error": "..."} with exit code 1.

Notes on schema:
  - DexScreener returns flat pair dicts with `priceUsd`, `liquidity.usd`,
    `volume.h24`, `txns.h24.buys/sells`, `priceChange.h1/h24`, `fdv`,
    `marketCap`, and (for some tokens) `info.socials/websites`.
  - GeckoTerminal uses JSON:API with `data`/`included`. We normalize to a
    flat shape close to DexScreener's so downstream agents see one contract.
  - Neither provider exposes a fully reliable honeypot / tax indicator —
    we surface what the providers do expose (24h buy/sell tx count, liquidity
    depth, price-change asymmetry) so the caller can judge.
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

DEXSC = "https://api.dexscreener.com"
GT = "https://api.geckoterminal.com/api/v2"

# Chain name normalization. DexScreener uses long names (ethereum, bsc,
# solana, polygon, arbitrum, base, ...); GeckoTerminal uses short slugs
# (eth, bsc, solana, polygon_pos, arbitrum, base, ...). Pass through if not
# in the map.
DEXSC_TO_GT = {
    "ethereum": "eth",
    "bsc": "bsc",
    "solana": "solana",
    "polygon": "polygon_pos",
    "arbitrum": "arbitrum",
    "base": "base",
    "optimism": "optimism",
    "avalanche": "avax",
    "fantom": "ftm",
    "linea": "linea",
    "blast": "blast",
    "sui": "sui",
    "ton": "ton",
    "tron": "tron",
    "cronos": "cro",
    "celo": "celo",
}
GT_TO_DEXSC = {v: k for k, v in DEXSC_TO_GT.items()}


def die(msg: str, code: int = 1) -> NoReturn:
    print(json.dumps({"error": msg}, ensure_ascii=False))
    sys.exit(code)


def _get_json(url: str, timeout: int = TIMEOUT) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _try(fn, *args, **kw):
    """Soft-fail wrapper: return (result, None) on success, (None, err_str) on
    HTTPError / URLError / timeout / JSON decode error. Never raises."""
    try:
        return fn(*args, **kw), None
    except urllib.error.HTTPError as e:
        return None, f"http {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return None, f"network: {e.reason}"
    except (json.JSONDecodeError, TimeoutError) as e:
        return None, f"decode: {e}"
    except Exception as e:  # noqa: BLE001  defensive — never let one provider sink the caller
        return None, f"unexpected: {type(e).__name__}: {e}"


# ---------- DexScreener ----------

def _ds_pair_norm(p: dict) -> dict:
    """Normalize a DexScreener pair dict to a flat shape."""
    base = p.get("baseToken") or {}
    quote = p.get("quoteToken") or {}
    liq = p.get("liquidity") or {}
    vol = p.get("volume") or {}
    pc = p.get("priceChange") or {}
    tx = p.get("txns") or {}
    tx24 = tx.get("h24") or {}
    info = p.get("info") or {}
    return {
        "chain": p.get("chainId"),
        "dex": p.get("dexId"),
        "pair_address": p.get("pairAddress"),
        "url": p.get("url"),
        "base": {
            "address": base.get("address"),
            "symbol": base.get("symbol"),
            "name": base.get("name"),
        },
        "quote": {
            "address": quote.get("address"),
            "symbol": quote.get("symbol"),
            "name": quote.get("name"),
        },
        "price_usd": float(p["priceUsd"]) if p.get("priceUsd") else None,
        "price_native": float(p["priceNative"]) if p.get("priceNative") else None,
        "liquidity_usd": liq.get("usd"),
        "liquidity_base": liq.get("base"),
        "liquidity_quote": liq.get("quote"),
        "volume_h24": vol.get("h24"),
        "volume_h6": vol.get("h6"),
        "volume_h1": vol.get("h1"),
        "price_change_h1_pct": pc.get("h1"),
        "price_change_h6_pct": pc.get("h6"),
        "price_change_h24_pct": pc.get("h24"),
        "txns_h24_buys": tx24.get("buys"),
        "txns_h24_sells": tx24.get("sells"),
        "fdv_usd": p.get("fdv"),
        "market_cap_usd": p.get("marketCap"),
        "pair_created_ms": p.get("pairCreatedAt"),
        "socials": info.get("socials"),
        "websites": info.get("websites"),
        "source": "dexscreener",
    }


def ds_search(q: str) -> list[dict]:
    qs = urllib.parse.urlencode({"q": q})
    j = _get_json(f"{DEXSC}/latest/dex/search?{qs}")
    return [_ds_pair_norm(p) for p in (j or {}).get("pairs", []) or []]


def ds_token(chain: str | None, addr: str) -> list[dict]:
    # DexScreener accepts plain token address (cross-chain) OR chain+pair.
    # The token endpoint takes any address and returns pairs across chains;
    # we'll filter by chain client-side if requested.
    j = _get_json(f"{DEXSC}/latest/dex/tokens/{addr}")
    pairs = [_ds_pair_norm(p) for p in (j or {}).get("pairs", []) or []]
    if chain:
        pairs = [p for p in pairs if (p.get("chain") or "").lower() == chain.lower()]
    return pairs


def ds_pair(chain: str, pair_addr: str) -> list[dict]:
    j = _get_json(f"{DEXSC}/latest/dex/pairs/{chain}/{pair_addr}")
    return [_ds_pair_norm(p) for p in (j or {}).get("pairs", []) or []]


def ds_boosted() -> list[dict]:
    # token-boosts/latest = trending paid boosts; closest analogue to "what's hot".
    j = _get_json(f"{DEXSC}/token-boosts/latest/v1")
    rows = j if isinstance(j, list) else []
    return [
        {
            "chain": r.get("chainId"),
            "token_address": r.get("tokenAddress"),
            "url": r.get("url"),
            "boost_amount": r.get("amount"),
            "boost_total": r.get("totalAmount"),
            "icon": r.get("icon"),
            "description": r.get("description"),
            "links": r.get("links"),
            "source": "dexscreener",
        }
        for r in rows
    ]


# ---------- GeckoTerminal (fallback) ----------

def _gt_pool_norm(pool: dict, included_index: dict, net_hint: str | None = None) -> dict:
    """Normalize a GeckoTerminal pool resource (JSON:API) to the flat shape.

    `net_hint` is the GeckoTerminal network slug used in the URL when known;
    used to fill `chain` when relationships don't carry it (trending_pools)."""
    a = pool.get("attributes") or {}
    rel = pool.get("relationships") or {}

    def _included(kind: str, key: str = "data") -> dict:
        rd = (rel.get(kind) or {}).get(key) or {}
        if isinstance(rd, list):
            rd = rd[0] if rd else {}
        rid = rd.get("id")
        return (included_index.get((rd.get("type"), rid)) or {}).get("attributes") or {}

    base_t = _included("base_token")
    quote_t = _included("quote_token")
    dex = _included("dex")
    rel_net_id = (rel.get("network") or {}).get("data", {}).get("id")
    # Pool resource id is sometimes `{network}_{address}`; pull the prefix
    # when network rel is missing.
    pool_id = pool.get("id") or ""
    pool_net = pool_id.split("_", 1)[0] if "_" in pool_id else None
    gt_net = rel_net_id or pool_net or net_hint
    pc = a.get("price_change_percentage") or {}
    vol = a.get("volume_usd") or {}
    tx = a.get("transactions") or {}
    tx24 = tx.get("h24") or {}
    return {
        "chain": GT_TO_DEXSC.get(gt_net, gt_net),
        "dex": (a.get("dex_id") or (dex.get("name") if dex else None) or
                (rel.get("dex") or {}).get("data", {}).get("id")),
        "pair_address": a.get("address"),
        "url": f"https://www.geckoterminal.com/{gt_net}/pools/{a.get('address')}" if a.get("address") and gt_net else None,
        "base": {
            "address": base_t.get("address"),
            "symbol": base_t.get("symbol"),
            "name": base_t.get("name"),
        },
        "quote": {
            "address": quote_t.get("address"),
            "symbol": quote_t.get("symbol"),
            "name": quote_t.get("name"),
        },
        "price_usd": float(a["base_token_price_usd"]) if a.get("base_token_price_usd") else None,
        "price_native": float(a["base_token_price_native_currency"]) if a.get("base_token_price_native_currency") else None,
        "liquidity_usd": float(a["reserve_in_usd"]) if a.get("reserve_in_usd") else None,
        "liquidity_base": None,
        "liquidity_quote": None,
        "volume_h24": float(vol["h24"]) if vol.get("h24") else None,
        "volume_h6": float(vol["h6"]) if vol.get("h6") else None,
        "volume_h1": float(vol["h1"]) if vol.get("h1") else None,
        "price_change_h1_pct": float(pc["h1"]) if pc.get("h1") else None,
        "price_change_h6_pct": float(pc["h6"]) if pc.get("h6") else None,
        "price_change_h24_pct": float(pc["h24"]) if pc.get("h24") else None,
        "txns_h24_buys": (tx24.get("buys") if isinstance(tx24, dict) else None),
        "txns_h24_sells": (tx24.get("sells") if isinstance(tx24, dict) else None),
        "fdv_usd": float(a["fdv_usd"]) if a.get("fdv_usd") else None,
        "market_cap_usd": float(a["market_cap_usd"]) if a.get("market_cap_usd") else None,
        "pair_created_ms": None,
        "name": a.get("name"),
        "source": "geckoterminal",
    }


def _gt_index(payload: dict) -> dict:
    return {(r.get("type"), r.get("id")): r for r in payload.get("included", []) or []}


def gt_search(q: str) -> list[dict]:
    qs = urllib.parse.urlencode({"query": q, "page": 1, "include": "base_token,quote_token,network,dex"})
    j = _get_json(f"{GT}/search/pools?{qs}")
    idx = _gt_index(j)
    return [_gt_pool_norm(r, idx) for r in (j or {}).get("data", []) or []]


def gt_token(chain: str, addr: str) -> list[dict]:
    net = DEXSC_TO_GT.get(chain.lower(), chain.lower())
    # /networks/{net}/tokens/{addr}/pools returns pools for the token
    qs = urllib.parse.urlencode({"page": 1, "include": "base_token,quote_token,network,dex"})
    j = _get_json(f"{GT}/networks/{net}/tokens/{addr}/pools?{qs}")
    idx = _gt_index(j)
    return [_gt_pool_norm(r, idx, net_hint=net) for r in (j or {}).get("data", []) or []]


def gt_pair(chain: str, pair_addr: str) -> list[dict]:
    net = DEXSC_TO_GT.get(chain.lower(), chain.lower())
    qs = urllib.parse.urlencode({"include": "base_token,quote_token,network,dex"})
    j = _get_json(f"{GT}/networks/{net}/pools/{pair_addr}?{qs}")
    idx = _gt_index(j)
    data = (j or {}).get("data")
    if not data:
        return []
    rows = data if isinstance(data, list) else [data]
    return [_gt_pool_norm(r, idx, net_hint=net) for r in rows]


def gt_trending(chain: str | None) -> list[dict]:
    inc = urllib.parse.urlencode({"page": 1, "include": "base_token,quote_token,network,dex"})
    if chain:
        net = DEXSC_TO_GT.get(chain.lower(), chain.lower())
        url = f"{GT}/networks/{net}/trending_pools?{inc}"
        j = _get_json(url)
        idx = _gt_index(j)
        return [_gt_pool_norm(r, idx, net_hint=net) for r in (j or {}).get("data", []) or []]
    url = f"{GT}/networks/trending_pools?{inc}"
    j = _get_json(url)
    idx = _gt_index(j)
    return [_gt_pool_norm(r, idx) for r in (j or {}).get("data", []) or []]


# ---------- public commands (primary -> fallback) ----------

def cmd_search(args):
    """Search DEX pairs by token name/symbol/address.

    DexScreener first; on empty/error, GeckoTerminal."""
    primary, err = _try(ds_search, args.query)
    if primary:
        rows = primary
        provider = "dexscreener"
        fallback_used = False
    else:
        fb, ferr = _try(gt_search, args.query)
        if fb:
            rows = fb
            provider = "geckoterminal"
            fallback_used = True
        elif err and ferr:
            die(f"both providers failed: dexscreener={err}; geckoterminal={ferr}")
        else:
            rows = []
            provider = "dexscreener" if not err else "geckoterminal"
            fallback_used = bool(err)
    # Sort by liquidity_usd desc for usefulness; limit.
    rows.sort(key=lambda r: r.get("liquidity_usd") or 0, reverse=True)
    return {
        "query": args.query,
        "provider": provider,
        "fallback_used": fallback_used,
        "count": len(rows),
        "pairs": rows[: args.limit],
    }


def cmd_contract(args):
    """All DEX pairs for a token contract on a given chain.

    Returns enough fields for tax/honeypot heuristics: 24h buy/sell tx count,
    liquidity, price-change asymmetry. Caller decides the verdict — neither
    provider tags 'honeypot'.

    Chain is required for the primary path; if omitted, falls back to the
    cross-chain DexScreener tokens endpoint."""
    chain = (args.chain or "").lower() or None
    addr = args.address
    primary, err = _try(ds_token, chain, addr)
    if primary:
        rows = primary
        provider = "dexscreener"
        fallback_used = False
    elif chain:
        fb, ferr = _try(gt_token, chain, addr)
        if fb:
            rows = fb
            provider = "geckoterminal"
            fallback_used = True
        elif err and ferr:
            die(f"both providers failed: dexscreener={err}; geckoterminal={ferr}")
        else:
            rows = []
            provider = "dexscreener" if not err else "geckoterminal"
            fallback_used = bool(err)
    else:
        # No chain → no GT fallback path (GT requires chain).
        rows = []
        provider = "dexscreener"
        fallback_used = False
        if err:
            die(f"dexscreener failed and no chain provided for fallback: {err}")
    rows.sort(key=lambda r: r.get("liquidity_usd") or 0, reverse=True)
    return {
        "chain": chain,
        "address": addr,
        "provider": provider,
        "fallback_used": fallback_used,
        "count": len(rows),
        "pairs": rows[: args.limit],
    }


def cmd_pair(args):
    """Lookup one specific pair by chain + pair address."""
    primary, err = _try(ds_pair, args.chain, args.pair_address)
    if primary:
        rows = primary
        provider = "dexscreener"
        fallback_used = False
    else:
        fb, ferr = _try(gt_pair, args.chain, args.pair_address)
        if fb:
            rows = fb
            provider = "geckoterminal"
            fallback_used = True
        elif err and ferr:
            die(f"both providers failed: dexscreener={err}; geckoterminal={ferr}")
        else:
            rows = []
            provider = "dexscreener" if not err else "geckoterminal"
            fallback_used = bool(err)
    return {
        "chain": args.chain,
        "pair_address": args.pair_address,
        "provider": provider,
        "fallback_used": fallback_used,
        "pairs": rows,
    }


def cmd_trending(args):
    """Trending pools — optionally scoped to one chain.

    DexScreener's nearest analogue is 'boosted tokens' (paid promotion list).
    Where the caller wants real volume-based trending, fall back to
    GeckoTerminal's trending_pools, which is curated by their algorithm."""
    if args.source == "geckoterminal":
        rows, err = _try(gt_trending, args.chain)
        if err:
            die(f"geckoterminal: {err}")
        rows = rows or []
        return {
            "chain": args.chain,
            "provider": "geckoterminal",
            "fallback_used": False,
            "count": len(rows),
            "pools": rows[: args.limit],
        }
    # default: dexscreener boosts first; gt trending on empty/error
    primary, err = _try(ds_boosted)
    if primary:
        rows = primary
        if args.chain:
            rows = [r for r in rows if (r.get("chain") or "").lower() == args.chain.lower()]
        if rows:
            return {
                "chain": args.chain,
                "provider": "dexscreener",
                "fallback_used": False,
                "count": len(rows),
                "pools": rows[: args.limit],
            }
    fb, ferr = _try(gt_trending, args.chain)
    if fb:
        return {
            "chain": args.chain,
            "provider": "geckoterminal",
            "fallback_used": True,
            "count": len(fb),
            "pools": fb[: args.limit],
        }
    if err and ferr:
        die(f"both providers failed: dexscreener={err}; geckoterminal={ferr}")
    return {
        "chain": args.chain,
        "provider": "geckoterminal",
        "fallback_used": True,
        "count": 0,
        "pools": [],
    }


def cmd_networks(args):
    """List supported chain identifiers as seen by each provider."""
    return {
        "dexscreener_to_geckoterminal": DEXSC_TO_GT,
        "note": "Pass through if a chain id is not in the map. Use 'ethereum' / 'bsc' / 'solana' / etc. for --chain.",
    }


def main() -> None:
    p = argparse.ArgumentParser(prog="dex.py", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("search", help="search DEX pairs by token name/symbol/address")
    ps.add_argument("query", help="free-text token name / symbol / address")
    ps.add_argument("--limit", type=int, default=20)
    ps.set_defaults(func=cmd_search)

    pc = sub.add_parser("contract", help="all DEX pairs for a token contract")
    pc.add_argument("address", help="token contract address")
    pc.add_argument("--chain", default="", help="chain id (ethereum/bsc/solana/...). Optional for cross-chain DexScreener lookup, required for GeckoTerminal fallback.")
    pc.add_argument("--limit", type=int, default=20)
    pc.set_defaults(func=cmd_contract)

    pp = sub.add_parser("pair", help="lookup one specific pair by chain + pair address")
    pp.add_argument("chain", help="chain id (ethereum/bsc/solana/...)")
    pp.add_argument("pair_address", help="pair contract address")
    pp.set_defaults(func=cmd_pair)

    pt = sub.add_parser("trending", help="trending DEX pools (DexScreener boosts; GT trending fallback)")
    pt.add_argument("--chain", default="", help="optional chain filter (ethereum/bsc/solana/...)")
    pt.add_argument("--limit", type=int, default=15)
    pt.add_argument("--source", choices=("auto", "geckoterminal"), default="auto",
                    help="auto = DexScreener boosts then GT trending; geckoterminal = GT only (volume-based)")
    pt.set_defaults(func=cmd_trending)

    pn = sub.add_parser("networks", help="list chain id mapping")
    pn.set_defaults(func=cmd_networks)

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
