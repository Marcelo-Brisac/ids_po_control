#!/usr/bin/env python3
"""global-markets / futures: front-month quotes for global commodity, equity-
index, rates, and vol futures (NYMEX, COMEX, NYBOT, CBOT, CME, CFE).

Keyless. Providers:
  - futsseapi.eastmoney.com/static/{sc}_{root}00Y_qt    (primary for NYMEX/COMEX/NYBOT)
  - query1.finance.yahoo.com/v8/finance/chart           (fallback; primary for CBOT/CME/CFE)

For CN onshore (SHFE/DCE/CZCE/INE/GFEX) futures, use cn-markets/scripts/futures.py.

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
EM_STATIC = "http://futsseapi.eastmoney.com/static/{sc}_{dm}_qt"
YH_CHART = "https://query1.finance.yahoo.com/v8/finance/chart"

# Each entry: alias → (description, exchange, sc, cont, yahoo)
# cont = Eastmoney continuous-month code ({root}00Y); None if not on futsseapi.
# yahoo = Yahoo Finance =F continuous symbol; primary when sc is None.
CATALOG: dict[str, dict[str, Any]] = {
    # Energy (NYMEX)
    "CL":  {"name": "WTI Crude Oil",        "exchange": "NYMEX", "sc": 102, "cont": "CL00Y",  "yahoo": "CL=F"},
    "BZ":  {"name": "Brent Crude",          "exchange": "NYMEX", "sc": 102, "cont": "BZ00Y",  "yahoo": "BZ=F"},
    "NG":  {"name": "Natural Gas",          "exchange": "NYMEX", "sc": 102, "cont": "NG00Y",  "yahoo": "NG=F"},
    "RB":  {"name": "RBOB Gasoline",        "exchange": "NYMEX", "sc": 102, "cont": "RB00Y",  "yahoo": "RB=F"},
    "HO":  {"name": "Heating Oil",          "exchange": "NYMEX", "sc": 102, "cont": "HO00Y",  "yahoo": "HO=F"},
    # Metals (COMEX/NYMEX)
    "GC":  {"name": "COMEX Gold",           "exchange": "COMEX", "sc": 101, "cont": "GC00Y",  "yahoo": "GC=F"},
    "SI":  {"name": "COMEX Silver",         "exchange": "COMEX", "sc": 101, "cont": "SI00Y",  "yahoo": "SI=F"},
    "HG":  {"name": "COMEX Copper",         "exchange": "COMEX", "sc": 101, "cont": "HG00Y",  "yahoo": "HG=F"},
    "PL":  {"name": "Platinum",             "exchange": "NYMEX", "sc": 102, "cont": "PL00Y",  "yahoo": "PL=F"},
    "PA":  {"name": "Palladium",            "exchange": "NYMEX", "sc": 102, "cont": "PA00Y",  "yahoo": "PA=F"},
    # Soft / agri (NYBOT)
    "SB":  {"name": "Sugar #11",            "exchange": "NYBOT", "sc": 108, "cont": "SB00Y",  "yahoo": "SB=F"},
    "CT":  {"name": "Cotton #2",            "exchange": "NYBOT", "sc": 108, "cont": "CT00Y",  "yahoo": "CT=F"},
    "KC":  {"name": "Coffee C",             "exchange": "NYBOT", "sc": 108, "cont": "KC00Y",  "yahoo": "KC=F"},
    "CC":  {"name": "Cocoa",                "exchange": "NYBOT", "sc": 108, "cont": "CC00Y",  "yahoo": "CC=F"},
    # Grains (CBOT — Eastmoney sc=103 covers these)
    "ZC":  {"name": "Corn",                 "exchange": "CBOT",  "sc": 103, "cont": "ZC00Y",  "yahoo": "ZC=F"},
    "ZW":  {"name": "Wheat",                "exchange": "CBOT",  "sc": 103, "cont": "ZW00Y",  "yahoo": "ZW=F"},
    "ZS":  {"name": "Soybean",              "exchange": "CBOT",  "sc": 103, "cont": "ZS00Y",  "yahoo": "ZS=F"},
    "ZL":  {"name": "Soybean Oil",          "exchange": "CBOT",  "sc": 103, "cont": "ZL00Y",  "yahoo": "ZL=F"},
    "ZM":  {"name": "Soybean Meal",         "exchange": "CBOT",  "sc": 103, "cont": "ZM00Y",  "yahoo": "ZM=F"},
    # Equity index (CME — sc=103 covers ES/NQ/YM; RTY is Yahoo-only)
    "ES":  {"name": "S&P 500 E-mini",       "exchange": "CME",   "sc": 103, "cont": "ES00Y",  "yahoo": "ES=F"},
    "NQ":  {"name": "Nasdaq 100 E-mini",    "exchange": "CME",   "sc": 103, "cont": "NQ00Y",  "yahoo": "NQ=F"},
    "YM":  {"name": "Dow E-mini",           "exchange": "CME",   "sc": 103, "cont": "YM00Y",  "yahoo": "YM=F"},
    "RTY": {"name": "Russell 2000 E-mini",  "exchange": "CME",   "sc": None, "cont": None,    "yahoo": "RTY=F"},
    # Rates (CBOT — Yahoo only)
    "ZN":  {"name": "10Y US T-Note",        "exchange": "CBOT",  "sc": None, "cont": None,    "yahoo": "ZN=F"},
    "ZB":  {"name": "30Y US T-Bond",        "exchange": "CBOT",  "sc": None, "cont": None,    "yahoo": "ZB=F"},
    "ZF":  {"name": "5Y US T-Note",         "exchange": "CBOT",  "sc": None, "cont": None,    "yahoo": "ZF=F"},
    "ZT":  {"name": "2Y US T-Note",         "exchange": "CBOT",  "sc": None, "cont": None,    "yahoo": "ZT=F"},
    # FX index / vol
    "DX":  {"name": "US Dollar Index",      "exchange": "ICE",   "sc": None, "cont": None,    "yahoo": "DX=F"},
    "VX":  {"name": "VIX Future",           "exchange": "CFE",   "sc": None, "cont": None,    "yahoo": "VX=F"},
}


def die(msg: str, code: int = 1) -> NoReturn:
    print(json.dumps({"error": msg}, ensure_ascii=False))
    sys.exit(code)


def _get_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def em_quote_one(sc: int, cont: str) -> dict[str, Any] | None:
    url = EM_STATIC.format(sc=sc, dm=cont)
    try:
        j = _get_json(url)
    except (urllib.error.URLError, OSError):
        return None
    qt = j.get("qt") if isinstance(j, dict) else None
    if not qt or qt.get("p") in (None, 0, "-"):
        return None
    return {
        "name": qt.get("name"),
        "code": qt.get("dm"),
        "price": qt.get("p"),
        "open": qt.get("o"),
        "high": qt.get("h"),
        "low": qt.get("l"),
        "prev_close": qt.get("zjsj"),
        "change": qt.get("zde"),
        "pct": qt.get("zdf"),
        "volume": qt.get("vol"),
        "open_interest": qt.get("ccl"),
        "source": "eastmoney",
    }


def yh_quote_one(yahoo_sym: str) -> dict[str, Any] | None:
    url = f"{YH_CHART}/{urllib.parse.quote(yahoo_sym)}?range=5d&interval=1d"
    try:
        j = _get_json(url)
    except (urllib.error.URLError, OSError):
        return None
    try:
        r = j["chart"]["result"][0]
        meta = r["meta"]
        price = meta.get("regularMarketPrice")
        prev = meta.get("chartPreviousClose") or meta.get("previousClose")
        if price is None:
            return None
        change = (price - prev) if prev else None
        pct = (change / prev * 100) if (change is not None and prev) else None
        return {
            "name": meta.get("longName") or meta.get("shortName") or yahoo_sym,
            "code": yahoo_sym,
            "price": price,
            "open": None,
            "high": meta.get("regularMarketDayHigh"),
            "low": meta.get("regularMarketDayLow"),
            "prev_close": prev,
            "change": round(change, 6) if change is not None else None,
            "pct": round(pct, 4) if pct is not None else None,
            "volume": meta.get("regularMarketVolume"),
            "open_interest": None,
            "source": "yahoo",
        }
    except (KeyError, IndexError, TypeError):
        return None


def cmd_quote(args):
    aliases = [a.strip() for a in args.aliases.split(",") if a.strip()]
    out = []
    for a in aliases:
        entry = CATALOG.get(a)
        if not entry:
            out.append({"alias": a, "error": "unknown contract alias"})
            continue
        row: dict[str, Any] | None = None
        if entry["sc"] and entry["cont"] and args.source != "yahoo":
            row = em_quote_one(entry["sc"], entry["cont"])
        if (row is None or args.source == "yahoo") and entry["yahoo"]:
            yh = yh_quote_one(entry["yahoo"])
            if yh:
                row = yh
        if row is None:
            row = {"alias": a, "error": "all sources failed"}
        row.setdefault("alias", a)
        row.setdefault("desc", entry["name"])
        out.append(row)
    return out


def cmd_list(args):
    return [
        {
            "alias": alias,
            "name": e["name"],
            "exchange": e["exchange"],
            "eastmoney_code": e["cont"],
            "yahoo_symbol": e["yahoo"],
        }
        for alias, e in CATALOG.items()
    ]


def main() -> None:
    p = argparse.ArgumentParser(prog="futures.py", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    pq = sub.add_parser("quote", help="front-month quote for one or more contract aliases")
    pq.add_argument("aliases", help="comma-separated aliases (e.g. CL,GC,ES). See `list`.")
    pq.add_argument("--source", choices=["auto", "eastmoney", "yahoo"], default="auto")
    pq.set_defaults(func=cmd_quote)
    pl = sub.add_parser("list", help="list supported contract aliases")
    pl.set_defaults(func=cmd_list)
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
