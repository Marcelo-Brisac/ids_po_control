#!/usr/bin/env python3
"""global-markets / options: listed option chains for US/global equities,
ETFs, and index options (SPX, NDX, RUT, VIX, etc.).

Provider: yfinance. Lazy-imported — install only if needed:

    uv sync --frozen   # at skill root; then invoke via `uv run scripts/options.py …`

Subcommands cover expiry discovery, full-chain pulls (calls + puts at all
strikes), single-contract quotes, and per-symbol IV / volume snapshots.

Output: JSON to stdout. Errors: JSON {"error": "..."} with exit code 1.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, NoReturn


def die(msg: str, *, install: str | None = None, code: int = 1) -> NoReturn:
    payload: dict[str, Any] = {"error": msg}
    if install:
        payload["install"] = install
    print(json.dumps(payload, ensure_ascii=False))
    sys.exit(code)


def _yf():
    try:
        import yfinance as yf  # type: ignore
    except ImportError:
        die("yfinance not installed", install="uv sync --frozen   # at skill root, then re-invoke via `uv run scripts/options.py …`", code=2)
    return yf


def _df_to_records(df) -> list[dict[str, Any]]:
    """DataFrame → list-of-dicts; NaN/NaT/pd.NA → None (dict-level sanitize)."""
    if df is None:
        return []
    try:
        if hasattr(df, "empty") and df.empty:
            return []
        import math
        import pandas as pd
        df2 = df.copy()
        for col in df2.columns:
            ser = df2[col]
            try:
                if hasattr(ser.dtype, "kind") and ser.dtype.kind == "M":
                    df2[col] = ser.dt.strftime("%Y-%m-%d").where(ser.notna(), None)
            except Exception:
                pass
        records = df2.to_dict(orient="records")
        out = []
        for rec in records:
            clean = {}
            for k, v in rec.items():
                if v is None:
                    clean[k] = None
                elif isinstance(v, float) and math.isnan(v):
                    clean[k] = None
                elif v is pd.NaT or v == "NaT":
                    clean[k] = None
                else:
                    try:
                        if pd.isna(v):
                            clean[k] = None
                            continue
                    except (TypeError, ValueError):
                        pass
                    clean[k] = v
            out.append(clean)
        return out
    except Exception:
        return []


def cmd_expiries(args):
    yf = _yf()
    t = yf.Ticker(args.symbol)
    return {
        "symbol": args.symbol.upper(),
        "expiries": list(t.options) if hasattr(t, "options") and t.options else [],
        "source": "yfinance",
    }


def cmd_chain(args):
    yf = _yf()
    t = yf.Ticker(args.symbol)
    expiries = list(t.options) if t.options else []
    if not expiries:
        return {"symbol": args.symbol.upper(), "error": "no listed options"}
    expiry = args.expiry or expiries[0]
    if expiry not in expiries:
        return {
            "symbol": args.symbol.upper(),
            "error": f"expiry {expiry!r} not listed",
            "available": expiries,
        }
    chain = t.option_chain(expiry)
    out: dict[str, Any] = {
        "symbol": args.symbol.upper(),
        "expiry": expiry,
        "underlying_price": getattr(chain, "underlying", {}).get("regularMarketPrice") if hasattr(chain, "underlying") else None,
        "source": "yfinance",
    }
    if args.strike_range:
        try:
            lo, hi = (float(x) for x in args.strike_range.split(":"))
            calls = chain.calls[(chain.calls["strike"] >= lo) & (chain.calls["strike"] <= hi)]
            puts = chain.puts[(chain.puts["strike"] >= lo) & (chain.puts["strike"] <= hi)]
        except Exception:
            calls, puts = chain.calls, chain.puts
    else:
        calls, puts = chain.calls, chain.puts
    out["calls"] = _df_to_records(calls)
    out["puts"] = _df_to_records(puts)
    out["call_count"] = len(out["calls"])
    out["put_count"] = len(out["puts"])
    return out


def cmd_quote(args):
    """Single-contract quote: SYM EXPIRY STRIKE TYPE (C/P)."""
    yf = _yf()
    t = yf.Ticker(args.symbol)
    expiries = list(t.options) if t.options else []
    if args.expiry not in expiries:
        return {"symbol": args.symbol.upper(), "error": f"expiry {args.expiry!r} not listed", "available": expiries}
    chain = t.option_chain(args.expiry)
    side = chain.calls if args.type.upper() == "C" else chain.puts
    strike = float(args.strike)
    match = side[side["strike"] == strike]
    if match.empty:
        avail = sorted(side["strike"].tolist())
        return {
            "symbol": args.symbol.upper(), "expiry": args.expiry, "type": args.type.upper(),
            "error": f"strike {strike} not listed",
            "nearest_strikes": [s for s in avail if abs(s - strike) <= 50][:10],
        }
    rec = _df_to_records(match)[0]
    rec.update({"symbol": args.symbol.upper(), "expiry": args.expiry, "side": args.type.upper(), "source": "yfinance"})
    return rec


def cmd_iv_snapshot(args):
    """At-the-money IV across all listed expiries (term structure)."""
    yf = _yf()
    t = yf.Ticker(args.symbol)
    expiries = list(t.options) if t.options else []
    if not expiries:
        return {"symbol": args.symbol.upper(), "error": "no listed options"}
    info = t.info or {}
    spot = info.get("regularMarketPrice") or info.get("currentPrice")
    if spot is None:
        return {"symbol": args.symbol.upper(), "error": "no spot price available"}
    out: list[dict[str, Any]] = []
    for exp in expiries[: args.limit]:
        try:
            chain = t.option_chain(exp)
        except Exception:
            continue
        # ATM = strike closest to spot. Use call IV (puts should agree under put-call parity).
        try:
            calls = chain.calls
            if calls.empty:
                continue
            atm_row = calls.iloc[(calls["strike"] - spot).abs().argsort()[:1]]
            iv = float(atm_row["impliedVolatility"].iloc[0]) if "impliedVolatility" in atm_row else None
            strike = float(atm_row["strike"].iloc[0])
            out.append({
                "expiry": exp,
                "atm_strike": strike,
                "call_iv": iv,
                "call_volume": int(atm_row["volume"].iloc[0]) if "volume" in atm_row and atm_row["volume"].iloc[0] == atm_row["volume"].iloc[0] else None,
                "call_oi": int(atm_row["openInterest"].iloc[0]) if "openInterest" in atm_row and atm_row["openInterest"].iloc[0] == atm_row["openInterest"].iloc[0] else None,
            })
        except Exception:
            continue
    return {
        "symbol": args.symbol.upper(),
        "spot": spot,
        "term_structure": out,
        "source": "yfinance",
    }


def main() -> None:
    p = argparse.ArgumentParser(prog="options.py", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    pe = sub.add_parser("expiries", help="list available option expiry dates")
    pe.add_argument("symbol")
    pe.set_defaults(func=cmd_expiries)

    pc = sub.add_parser("chain", help="full option chain (calls + puts) for one expiry")
    pc.add_argument("symbol")
    pc.add_argument("--expiry", help="YYYY-MM-DD; default = nearest")
    pc.add_argument("--strike-range", help="filter strikes, e.g. 180:220")
    pc.set_defaults(func=cmd_chain)

    pq = sub.add_parser("quote", help="single-contract quote: SYMBOL EXPIRY STRIKE TYPE")
    pq.add_argument("symbol")
    pq.add_argument("expiry", help="YYYY-MM-DD")
    pq.add_argument("strike")
    pq.add_argument("type", choices=["C", "c", "P", "p"], help="C(all) or P(ut)")
    pq.set_defaults(func=cmd_quote)

    pi = sub.add_parser("iv-snapshot", help="ATM IV across all listed expiries (term structure)")
    pi.add_argument("symbol")
    pi.add_argument("--limit", type=int, default=12, help="number of expiries to scan")
    pi.set_defaults(func=cmd_iv_snapshot)

    args = p.parse_args()
    try:
        out = args.func(args)
    except SystemExit:
        raise
    except Exception as e:
        die(f"{type(e).__name__}: {e}")
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
