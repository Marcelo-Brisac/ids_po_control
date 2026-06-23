#!/usr/bin/env python3
"""crypto-markets / derivatives: perpetual funding, open interest,
long/short ratios across Binance, Bybit, and OKX. Keyless. Stdlib only.

Symbol conventions per venue:
  - Binance perpetual: BTCUSDT, ETHUSDT     (USDT-margined linear)
  - Bybit linear:      BTCUSDT, ETHUSDT
  - OKX swap:          BTC-USDT-SWAP, ETH-USDT-SWAP

`funding <SYM>` and `oi <SYM>` accept a Binance-style pair and auto-
translate to each venue. For OKX, the script appends `-SWAP` and
inserts the dash. For exotic pairs not present on a venue, that venue
is skipped in the response (no error).

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

BINANCE_FAPI = "https://fapi.binance.com"
BYBIT = "https://api.bybit.com"
OKX = "https://www.okx.com"


def die(msg: str, code: int = 1) -> NoReturn:
    print(json.dumps({"error": msg}, ensure_ascii=False))
    sys.exit(code)


def _get_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _okx_inst(symbol: str) -> str:
    """BTCUSDT -> BTC-USDT-SWAP, ETHUSDC -> ETH-USDC-SWAP. Defaults to USDT split."""
    s = symbol.upper()
    for quote in ("USDT", "USDC", "USD"):
        if s.endswith(quote):
            return f"{s[:-len(quote)]}-{quote}-SWAP"
    return f"{s}-SWAP"


def _safe(fn):
    try:
        return fn()
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, KeyError, ValueError, IndexError):
        return None


def cmd_funding(args):
    """Current funding rate + next funding time across venues."""
    sym = args.symbol.upper()
    okx_inst = _okx_inst(sym)
    out: dict[str, Any] = {"symbol": sym, "venues": {}}

    def _binance():
        j = _get_json(f"{BINANCE_FAPI}/fapi/v1/premiumIndex?symbol={sym}")
        return {
            "mark_price": float(j["markPrice"]),
            "index_price": float(j["indexPrice"]),
            "funding_rate": float(j["lastFundingRate"]),
            "next_funding_time": int(j["nextFundingTime"]),
        }

    def _bybit():
        j = _get_json(f"{BYBIT}/v5/market/tickers?category=linear&symbol={sym}")
        rows = ((j.get("result") or {}).get("list")) or []
        if not rows:
            return None
        r = rows[0]
        return {
            "mark_price": float(r["markPrice"]),
            "index_price": float(r["indexPrice"]),
            "funding_rate": float(r["fundingRate"]),
            "next_funding_time": int(r["nextFundingTime"]),
        }

    def _okx():
        j = _get_json(f"{OKX}/api/v5/public/funding-rate?instId={okx_inst}")
        rows = j.get("data") or []
        if not rows:
            return None
        r = rows[0]
        return {
            "mark_price": None,
            "index_price": None,
            "funding_rate": float(r["fundingRate"]),
            "next_funding_time": int(r["nextFundingTime"]),
        }

    for name, fn in (("binance", _binance), ("bybit", _bybit), ("okx", _okx)):
        v = _safe(fn)
        if v is not None:
            out["venues"][name] = v

    # Aggregate funding rate (simple mean of available venues).
    rates = [v["funding_rate"] for v in out["venues"].values() if v.get("funding_rate") is not None]
    out["funding_rate_mean"] = sum(rates) / len(rates) if rates else None
    out["venues_count"] = len(out["venues"])
    return out


def cmd_funding_history(args):
    """Historical funding rates from one venue."""
    sym = args.symbol.upper()
    venue = args.venue.lower()
    if venue == "binance":
        j = _get_json(f"{BINANCE_FAPI}/fapi/v1/fundingRate?symbol={sym}&limit={args.limit}")
        rows = [
            {"timestamp": int(r["fundingTime"]), "funding_rate": float(r["fundingRate"])}
            for r in j
        ]
    elif venue == "bybit":
        j = _get_json(f"{BYBIT}/v5/market/funding/history?category=linear&symbol={sym}&limit={args.limit}")
        rows = [
            {"timestamp": int(r["fundingRateTimestamp"]), "funding_rate": float(r["fundingRate"])}
            for r in ((j.get("result") or {}).get("list") or [])
        ]
    elif venue == "okx":
        j = _get_json(f"{OKX}/api/v5/public/funding-rate-history?instId={_okx_inst(sym)}&limit={args.limit}")
        rows = [
            {"timestamp": int(r["fundingTime"]), "funding_rate": float(r["fundingRate"])}
            for r in (j.get("data") or [])
        ]
    else:
        return {"error": f"unknown venue {venue!r}", "valid": ["binance", "bybit", "okx"]}
    return {"symbol": sym, "venue": venue, "count": len(rows), "series": rows}


def cmd_oi(args):
    """Open interest snapshot across venues (sum in base units, USD notional when computable)."""
    sym = args.symbol.upper()
    okx_inst = _okx_inst(sym)
    out: dict[str, Any] = {"symbol": sym, "venues": {}}

    def _binance():
        j = _get_json(f"{BINANCE_FAPI}/fapi/v1/openInterest?symbol={sym}")
        return {"oi_contracts": float(j["openInterest"]), "timestamp": int(j["time"])}

    def _bybit():
        j = _get_json(f"{BYBIT}/v5/market/open-interest?category=linear&symbol={sym}&intervalTime=5min&limit=1")
        rows = ((j.get("result") or {}).get("list")) or []
        if not rows:
            return None
        return {"oi_contracts": float(rows[0]["openInterest"]), "timestamp": int(rows[0]["timestamp"])}

    def _okx():
        j = _get_json(f"{OKX}/api/v5/public/open-interest?instType=SWAP&instId={okx_inst}")
        rows = j.get("data") or []
        if not rows:
            return None
        r = rows[0]
        return {
            "oi_contracts": float(r["oi"]),
            "oi_ccy": float(r.get("oiCcy") or 0) or None,
            "oi_usd": float(r.get("oiUsd") or 0) or None,
            "timestamp": int(r["ts"]),
        }

    for name, fn in (("binance", _binance), ("bybit", _bybit), ("okx", _okx)):
        v = _safe(fn)
        if v is not None:
            out["venues"][name] = v

    total = sum(v.get("oi_contracts") or 0 for v in out["venues"].values())
    out["oi_contracts_sum"] = total if out["venues"] else None
    out["venues_count"] = len(out["venues"])
    return out


_LSR_PERIODS = {"5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"}


def cmd_lsr(args):
    """Long/short ratio (Binance — global accounts, top traders, taker)."""
    if args.period not in _LSR_PERIODS:
        return {"error": f"unknown period {args.period!r}", "valid": sorted(_LSR_PERIODS)}
    sym = args.symbol.upper()
    p = args.period

    def _fetch(path: str) -> list[dict[str, Any]]:
        url = f"{BINANCE_FAPI}/futures/data/{path}?symbol={sym}&period={p}&limit={args.limit}"
        rows = _get_json(url)
        return rows or []

    def _norm(rows, ratio_key, long_key="longAccount", short_key="shortAccount"):
        out = []
        for r in rows:
            out.append({
                "timestamp": int(r["timestamp"]),
                "ratio": float(r[ratio_key]) if r.get(ratio_key) is not None else None,
                "long": float(r[long_key]) if r.get(long_key) is not None else None,
                "short": float(r[short_key]) if r.get(short_key) is not None else None,
            })
        return out

    global_rows = _safe(lambda: _fetch("globalLongShortAccountRatio")) or []
    top_acc_rows = _safe(lambda: _fetch("topLongShortAccountRatio")) or []
    top_pos_rows = _safe(lambda: _fetch("topLongShortPositionRatio")) or []
    taker_rows = _safe(lambda: _fetch("takerlongshortRatio")) or []

    return {
        "symbol": sym,
        "period": p,
        "global_accounts": _norm(global_rows, "longShortRatio"),
        "top_traders_accounts": _norm(top_acc_rows, "longShortRatio"),
        "top_traders_positions": _norm(top_pos_rows, "longShortRatio"),
        "taker_buy_sell": [
            {
                "timestamp": int(r["timestamp"]),
                "ratio": float(r["buySellRatio"]) if r.get("buySellRatio") is not None else None,
                "buy_vol": float(r.get("buyVol") or 0) or None,
                "sell_vol": float(r.get("sellVol") or 0) or None,
            }
            for r in taker_rows
        ],
        "source": "binance_futures",
    }


def main() -> None:
    p = argparse.ArgumentParser(prog="derivatives.py", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    pf = sub.add_parser("funding", help="current funding rate across Binance/Bybit/OKX")
    pf.add_argument("symbol", help="Binance-style pair, e.g. BTCUSDT")
    pf.set_defaults(func=cmd_funding)

    pfh = sub.add_parser("funding-history", help="historical funding rates from one venue")
    pfh.add_argument("symbol")
    pfh.add_argument("--venue", default="binance", choices=["binance", "bybit", "okx"])
    pfh.add_argument("--limit", type=int, default=30)
    pfh.set_defaults(func=cmd_funding_history)

    po = sub.add_parser("oi", help="open interest snapshot across venues")
    po.add_argument("symbol")
    po.set_defaults(func=cmd_oi)

    pl = sub.add_parser("lsr", help="long/short ratios from Binance (global+top traders+taker)")
    pl.add_argument("symbol")
    pl.add_argument("--period", default="1h", help=f"one of: {sorted(_LSR_PERIODS)}")
    pl.add_argument("--limit", type=int, default=30)
    pl.set_defaults(func=cmd_lsr)

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
