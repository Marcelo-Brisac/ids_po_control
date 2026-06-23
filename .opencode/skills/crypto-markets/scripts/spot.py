#!/usr/bin/env python3
"""crypto-markets / spot: crypto spot prices, klines, market overview.

Keyless. Stdlib only. Providers:
  - Binance spot (api.binance.com)              — quote, klines, top symbols
  - CoinGecko free (api.coingecko.com)          — global mcap, top-N, trending
  - alternative.me                              — fear & greed index

Symbols: Binance pair format (BTCUSDT, ETHUSDT, ...). For non-USDT
quotes, just pass the full pair (e.g. BTCBUSD, ETHBTC).

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
TIMEOUT = 12
BN = "https://api.binance.com/api/v3"
CG = "https://api.coingecko.com/api/v3"
FNG = "https://api.alternative.me/fng/"


def die(msg: str, code: int = 1) -> NoReturn:
    print(json.dumps({"error": msg}, ensure_ascii=False))
    sys.exit(code)


def _get_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def cmd_quote(args):
    """24hr ticker for one or more pairs."""
    syms = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    # Binance batch endpoint accepts JSON array in query (no spaces — they
    # urlencode to '+' which Binance rejects).
    qs = urllib.parse.urlencode({"symbols": json.dumps(syms, separators=(",", ":"))})
    rows = _get_json(f"{BN}/ticker/24hr?{qs}")
    if isinstance(rows, dict):  # single returns dict, batch returns list
        rows = [rows]
    out = []
    for r in rows:
        out.append({
            "symbol": r["symbol"],
            "price": float(r["lastPrice"]),
            "open": float(r["openPrice"]),
            "high": float(r["highPrice"]),
            "low": float(r["lowPrice"]),
            "prev_close": float(r["prevClosePrice"]),
            "change": float(r["priceChange"]),
            "pct": float(r["priceChangePercent"]),
            "volume_base": float(r["volume"]),
            "volume_quote": float(r["quoteVolume"]),
            "trades": int(r["count"]),
        })
    return out


_INTERVALS = {"1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h",
              "12h", "1d", "3d", "1w", "1M"}


def cmd_klines(args):
    """OHLCV history for one pair."""
    if args.interval not in _INTERVALS:
        return {"error": f"unknown interval {args.interval!r}", "valid": sorted(_INTERVALS)}
    params = {"symbol": args.symbol.upper(), "interval": args.interval, "limit": str(args.limit)}
    rows = _get_json(f"{BN}/klines?{urllib.parse.urlencode(params)}")
    return {
        "symbol": args.symbol.upper(),
        "interval": args.interval,
        "count": len(rows),
        "klines": [
            {
                "open_time": r[0],
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": float(r[4]),
                "volume": float(r[5]),
                "close_time": r[6],
                "quote_volume": float(r[7]),
                "trades": int(r[8]),
            }
            for r in rows
        ],
        "source": "binance",
    }


def cmd_top(args):
    """Top-N coins by market cap (CoinGecko)."""
    params = {
        "vs_currency": args.vs.lower(),
        "order": "market_cap_desc",
        "per_page": str(args.limit),
        "page": "1",
        "sparkline": "false",
    }
    rows = _get_json(f"{CG}/coins/markets?{urllib.parse.urlencode(params)}")
    return [
        {
            "rank": r.get("market_cap_rank"),
            "id": r.get("id"),
            "symbol": (r.get("symbol") or "").upper(),
            "name": r.get("name"),
            "price": r.get("current_price"),
            "market_cap": r.get("market_cap"),
            "volume_24h": r.get("total_volume"),
            "pct_1h": (r.get("price_change_percentage_1h_in_currency")),
            "pct_24h": r.get("price_change_percentage_24h"),
            "pct_7d": r.get("price_change_percentage_7d_in_currency"),
            "ath": r.get("ath"),
            "ath_pct": r.get("ath_change_percentage"),
        }
        for r in rows
    ]


def cmd_global(args):
    """Global crypto market overview (total mcap, BTC dominance)."""
    j = _get_json(f"{CG}/global")
    d = j.get("data") or {}
    mcap = d.get("total_market_cap") or {}
    vol = d.get("total_volume") or {}
    dom = d.get("market_cap_percentage") or {}
    return {
        "active_cryptocurrencies": d.get("active_cryptocurrencies"),
        "markets": d.get("markets"),
        "total_market_cap_usd": mcap.get("usd"),
        "total_volume_usd": vol.get("usd"),
        "btc_dominance": dom.get("btc"),
        "eth_dominance": dom.get("eth"),
        "market_cap_change_pct_24h_usd": d.get("market_cap_change_percentage_24h_usd"),
        "updated_at": d.get("updated_at"),
        "source": "coingecko",
    }


def cmd_trending(args):
    """Trending coins / NFTs / categories on CoinGecko (last 24h search-weighted)."""
    j = _get_json(f"{CG}/search/trending")
    coins = []
    for c in (j.get("coins") or [])[: args.limit]:
        item = c.get("item") or {}
        coins.append({
            "rank": item.get("market_cap_rank"),
            "id": item.get("id"),
            "symbol": (item.get("symbol") or "").upper(),
            "name": item.get("name"),
            "price_btc": item.get("price_btc"),
            "score": item.get("score"),
        })
    return {"coins": coins, "source": "coingecko"}


def cmd_fear_greed(args):
    """Crypto Fear & Greed Index (alternative.me)."""
    j = _get_json(f"{FNG}?limit={args.limit}")
    rows = j.get("data") or []
    return {
        "count": len(rows),
        "series": [
            {
                "value": int(r["value"]),
                "classification": r.get("value_classification"),
                "timestamp": int(r["timestamp"]),
                "next_update_seconds": int(r.get("time_until_update") or 0) if i == 0 and r.get("time_until_update") else None,
            }
            for i, r in enumerate(rows)
        ],
        "source": "alternative.me",
    }


def main() -> None:
    p = argparse.ArgumentParser(prog="spot.py", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    pq = sub.add_parser("quote", help="24hr ticker for one or more Binance pairs")
    pq.add_argument("symbols", help="comma-separated pairs (e.g. BTCUSDT,ETHUSDT,SOLUSDT)")
    pq.set_defaults(func=cmd_quote)

    pk = sub.add_parser("klines", help="OHLCV history for one Binance pair")
    pk.add_argument("symbol")
    pk.add_argument("--interval", default="1d", help=f"one of: {sorted(_INTERVALS)}")
    pk.add_argument("--limit", type=int, default=200, help="rows (max 1000)")
    pk.set_defaults(func=cmd_klines)

    pt = sub.add_parser("top", help="top-N coins by market cap (CoinGecko)")
    pt.add_argument("--limit", type=int, default=20)
    pt.add_argument("--vs", default="usd", help="quote currency (usd, eur, cny, btc, eth, ...)")
    pt.set_defaults(func=cmd_top)

    pg = sub.add_parser("global", help="global market overview + BTC/ETH dominance")
    pg.set_defaults(func=cmd_global)

    ptr = sub.add_parser("trending", help="trending coins on CoinGecko (search-weighted, 24h)")
    ptr.add_argument("--limit", type=int, default=15)
    ptr.set_defaults(func=cmd_trending)

    pf = sub.add_parser("fear-greed", help="Crypto Fear & Greed Index (alternative.me)")
    pf.add_argument("--limit", type=int, default=1)
    pf.set_defaults(func=cmd_fear_greed)

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
