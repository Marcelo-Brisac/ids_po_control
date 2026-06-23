#!/usr/bin/env python3
"""global-equities skill: prices, history, search, FX for US-listed equities,
global indices, and major currency pairs.

Keyless. Providers (per data type):
  - api.nasdaq.com         (US stocks/ETFs, clean USD numbers)
  - push2.eastmoney.com    (indices + HK/JP/DE/etc.)
  - query1.finance.yahoo.com  (cross-market fallback; chart endpoint)
  - api.frankfurter.dev    (FX, ECB reference rates)

Fallback chains (per data type):
  US stock/ETF quote: Nasdaq → Yahoo → Eastmoney (105./106./107.)
  US stock/ETF history: Nasdaq → Yahoo → Eastmoney
  Index quote/history: Eastmoney → Yahoo (^GSPC, ^IXIC, ^DJI, ^HSI, ...)
  HK/JP/DE/KR quote: Eastmoney → Yahoo (TICKER.HK/.T/.DE/.KS)
  FX: Frankfurter → Yahoo (EURUSD=X)

Output: JSON to stdout. Errors: JSON {"error": "..."} with exit code 1.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from typing import Any, NoReturn

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
TIMEOUT = 15

NASDAQ_BASE = "https://api.nasdaq.com/api"
EM_QUOTE = "https://push2.eastmoney.com/api/qt/stock/get"
EM_KLINE = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
EM_SEARCH = "https://searchapi.eastmoney.com/api/suggest/get"
YH_CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
FX_BASE = "https://api.frankfurter.dev/v1"

# Map our secid prefixes / domain shorthands to Yahoo symbol suffixes.
# Yahoo uses: AAPL (bare US), 0700.HK, 7203.T, BMW.DE, 005930.KS, ^GSPC, etc.
YH_INDEX_FROM_ALIAS = {
    "SPX": "^GSPC", "NDX": "^NDX", "DJI": "^DJI", "DJIA": "^DJI",
    "HSI": "^HSI", "DAX": "^GDAXI", "GDAXI": "^GDAXI",
    "RUT": "^RUT", "FTSE": "^FTSE", "N225": "^N225",
    "HSCEI": "^HSCE", "HSTECH": "^HSTECH",
}
YH_EM_PREFIX_TO_SUFFIX = {
    "105": "",        # US Nasdaq → bare
    "106": "",        # US NYSE → bare
    "107": "",        # US AMEX/ETF → bare
    "116": ".HK",     # HK
    "133": ".T",      # Tokyo
    "155": ".L",      # London
    "196": ".KS",     # Korea
}

# Index name aliases (case-insensitive)
INDEX_ALIASES = {
    "SPX": "100.SPX",
    "S&P500": "100.SPX",
    "SP500": "100.SPX",
    "NDX": "100.NDX",
    "NASDAQ100": "100.NDX",
    "DJI": "100.DJIA",
    "DJIA": "100.DJIA",
    "DOW": "100.DJIA",
    "HSI": "100.HSI",
    "HANGSENG": "100.HSI",
    "DAX": "100.GDAXI",
    "GDAXI": "100.GDAXI",
    "RUT": "100.RUT",
    "RUSSELL2000": "100.RUT",
}

# Eastmoney quote field codes we ask for.
#   f43=last, f44=high, f45=low, f46=open, f47=volume, f48=amount,
#   f57=code, f58=name, f59=price_decimals (THE real scale hint — not f152),
#   f60=prev_close, f168=turnover_rate, f169=change_abs, f170=change_pct (bps).
# All price fields are integers scaled by 10^f59. Sample scales seen:
#   US stocks (105./106./107.) → f59=3 (price stored in milli-dollars)
#   HK stocks (116.)           → f59=3 (price stored in milli-HKD)
#   CN/global indices (100.)   → f59=2
#   A-share (0./1.)            → f59=2
EM_QUOTE_FIELDS = "f43,f44,f45,f46,f47,f48,f57,f58,f59,f60,f168,f169,f170"
EM_KLINE_FIELDS = (
    "f1=f1&f2=f2&f3=f3&f4=f4&f5=f5&f6=f6"
    "&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58"
)

# US asset class detection — caller-overridable but a good default
US_ETF_HINTS = {
    "SPY", "QQQ", "DIA", "IWM", "VOO", "VTI", "GLD", "SLV", "TLT", "HYG",
    "EEM", "EFA", "ARKK", "XLE", "XLF", "XLK", "XLY", "XLI", "XLP", "XLV",
    "XLU", "XLB", "XLRE", "XLC", "BND", "AGG", "VNQ", "USO", "UNG", "VXX",
}


# ---------- HTTP helpers ----------


def http_json(url: str, *, follow: bool = True) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        body = resp.read()
    return json.loads(body)


def die(msg: str, code: int = 1) -> NoReturn:
    print(json.dumps({"error": msg}), file=sys.stdout)
    sys.exit(code)


# ---------- Date helpers ----------


def resolve_range(args: argparse.Namespace) -> tuple[date, date]:
    """Resolve --from/--to or --days into (from, to) dates. `to` defaults to today."""
    today = date.today()
    if getattr(args, "days", None):
        return today - timedelta(days=args.days), today
    if not args.from_date or not args.to_date:
        die("must pass --from YYYY-MM-DD --to YYYY-MM-DD or --days N")
    return (
        datetime.strptime(args.from_date, "%Y-%m-%d").date(),
        datetime.strptime(args.to_date, "%Y-%m-%d").date(),
    )


# ---------- Eastmoney ----------


def _em_decimal(data: dict[str, Any]) -> int:
    # f59 is the price-decimals hint. f152 exists but is the *display* decimals
    # for the UI ("show 2 places"), not the raw scale; using it under-scales US
    # and HK prices by 10x. Default to 2 if missing.
    return int(data.get("f59") or 2)


def em_quote_one(secid: str) -> dict[str, Any]:
    url = f"{EM_QUOTE}?secid={secid}&fields={EM_QUOTE_FIELDS}"
    try:
        j = http_json(url)
        d = j.get("data")
        if not d:
            raise RuntimeError(f"no data rc={j.get('rc')}")
    except Exception as e:
        # Fallback to Yahoo for non-A-share secids we can map
        yh_sym = _yh_symbol_from_secid(secid)
        if yh_sym:
            y = yh_quote_one(yh_sym)
            if y:
                y["secid"] = secid
                y["fallback_reason"] = str(e)
                return y
        return {"symbol": secid, "error": str(e), "secid": secid}
    dec = _em_decimal(d)
    scale = 10**dec

    def num(k: str, factor: int = scale) -> float | None:
        v = d.get(k)
        if v is None or v == "-":
            return None
        try:
            return round(float(v) / factor, dec)
        except (TypeError, ValueError):
            return None

    last = num("f43")
    prev = num("f60")
    change = num("f169")
    pct = num("f170", 100)  # f170 is in basis points
    return {
        "symbol": d.get("f57"),
        "name": d.get("f58"),
        "secid": secid,
        "price": last,
        "open": num("f46"),
        "high": num("f44"),
        "low": num("f45"),
        "prev_close": prev,
        "change": change,
        "pct": pct,
        "volume": d.get("f47"),
        "amount": d.get("f48"),
        "source": "eastmoney",
    }


def em_quote(secids: list[str]) -> list[dict[str, Any]]:
    return [em_quote_one(s) for s in secids]


def em_history(secid: str, from_d: date, to_d: date) -> list[dict[str, Any]]:
    lmt = max((to_d - from_d).days + 1, 5)
    # klt: 101=daily, 102=weekly, 103=monthly. fqt=1: forward-adjusted.
    url = (
        f"{EM_KLINE}?secid={secid}&klt=101&fqt=1"
        f"&end={to_d.strftime('%Y%m%d')}&lmt={lmt}"
        "&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58"
    )
    try:
        j = http_json(url)
    except Exception:
        yh_sym = _yh_symbol_from_secid(secid)
        if yh_sym:
            r = yh_history(yh_sym, from_d, to_d)
            if r is not None:
                return r
        raise
    d = (j or {}).get("data") or {}
    klines = d.get("klines") or []
    if not klines:
        yh_sym = _yh_symbol_from_secid(secid)
        if yh_sym:
            r = yh_history(yh_sym, from_d, to_d)
            if r:
                return r
    rows: list[dict[str, Any]] = []
    for line in klines:
        # date,open,close,high,low,volume,amount,amplitude
        parts = line.split(",")
        if len(parts) < 6:
            continue
        d_str = parts[0]
        if d_str < from_d.strftime("%Y-%m-%d") or d_str > to_d.strftime("%Y-%m-%d"):
            continue
        rows.append(
            {
                "date": d_str,
                "open": float(parts[1]),
                "close": float(parts[2]),
                "high": float(parts[3]),
                "low": float(parts[4]),
                "volume": int(float(parts[5])),
            }
        )
    rows.sort(key=lambda r: r["date"], reverse=True)
    return rows


def em_search(query: str, limit: int = 10) -> list[dict[str, Any]]:
    qs = urllib.parse.urlencode({"input": query, "type": 14, "count": limit})
    url = f"{EM_SEARCH}?{qs}"
    j = http_json(url)
    data = ((j or {}).get("QuotationCodeTable") or {}).get("Data") or []
    out = []
    for row in data:
        out.append(
            {
                "symbol": row.get("Code"),
                "name": row.get("Name"),
                "secid": row.get("QuoteID"),
                "exchange": row.get("JYS"),
                "type": row.get("SecurityTypeName"),
            }
        )
    return out


# ---------- Nasdaq ----------


def _nasdaq_pick_assetclass(symbol: str) -> str:
    sym = symbol.upper()
    if sym in US_ETF_HINTS:
        return "etf"
    return "stocks"


def _to_float(v: Any) -> float | None:
    """Coerce an Any/str/None into float | None. 'N/A' → None."""
    if v is None or v == "N/A":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _nasdaq_dollar(v: str | None) -> float | None:
    if not v or v == "N/A":
        return None
    return float(v.replace("$", "").replace(",", "").strip())


def _nasdaq_int(v: str | None) -> int | None:
    if not v or v == "N/A":
        return None
    # Nasdaq occasionally returns volumes as fractional strings ("66579.633229")
    # for some ETF series — accept floats and truncate.
    s = v.replace(",", "").strip()
    try:
        return int(s)
    except ValueError:
        try:
            return int(float(s))
        except ValueError:
            return None


def nasdaq_quote_one(symbol: str) -> dict[str, Any]:
    assetclass = _nasdaq_pick_assetclass(symbol)
    url = f"{NASDAQ_BASE}/quote/{symbol}/info?assetclass={assetclass}"
    try:
        j = http_json(url)
        d = (j or {}).get("data")
        if not d:
            raise RuntimeError("nasdaq no data")
    except Exception as e:
        # Try Yahoo (bare US ticker) before Eastmoney
        y = yh_quote_one(symbol)
        if y:
            y["fallback_reason"] = str(e)
            return y
        return em_quote_one(_us_secid_guess(symbol)) | {"fallback_reason": str(e)}
    p = d.get("primaryData") or {}
    change_val = _to_float(p.get("netChange"))
    pct_raw = p.get("percentageChange")
    pct_val: float | None = None
    if pct_raw not in (None, "N/A"):
        pct_val = _to_float(str(pct_raw).rstrip("%"))
    return {
        "symbol": d.get("symbol"),
        "name": d.get("companyName"),
        "exchange": d.get("exchange"),
        "price": _nasdaq_dollar(p.get("lastSalePrice")),
        "change": change_val,
        "pct": pct_val,
        "volume": _nasdaq_int(p.get("volume")),
        "asof": p.get("lastTradeTimestamp"),
        "market_status": d.get("marketStatus"),
        "source": "nasdaq",
    }


def _us_secid_guess(symbol: str) -> str:
    # Eastmoney US market codes: 105 NASDAQ, 106 NYSE, 107 AMEX.
    # Without exchange info, default to 105; caller can re-search if needed.
    return f"105.{symbol.upper()}"


def nasdaq_quote(symbols: list[str]) -> list[dict[str, Any]]:
    return [nasdaq_quote_one(s) for s in symbols]


def nasdaq_history(symbol: str, from_d: date, to_d: date) -> list[dict[str, Any]]:
    assetclass = _nasdaq_pick_assetclass(symbol)
    fr = from_d.strftime("%Y-%m-%d")
    to = to_d.strftime("%Y-%m-%d")
    limit = max((to_d - from_d).days + 5, 10)
    url = (
        f"{NASDAQ_BASE}/quote/{symbol}/historical"
        f"?assetclass={assetclass}&fromdate={fr}&todate={to}&limit={limit}"
    )
    try:
        j = http_json(url)
    except Exception:
        # Try Yahoo before Eastmoney
        y = yh_history(symbol, from_d, to_d)
        if y:
            return y
        return em_history(_us_secid_guess(symbol), from_d, to_d)
    rows = (((j or {}).get("data") or {}).get("tradesTable") or {}).get("rows") or []
    if not rows:
        y = yh_history(symbol, from_d, to_d)
        if y:
            return y
        return em_history(_us_secid_guess(symbol), from_d, to_d)
    out = []
    for r in rows:
        try:
            mm, dd, yyyy = r["date"].split("/")
            iso = f"{yyyy}-{mm.zfill(2)}-{dd.zfill(2)}"
        except Exception:
            iso = r.get("date")
        out.append(
            {
                "date": iso,
                "open": _nasdaq_dollar(r.get("open")),
                "high": _nasdaq_dollar(r.get("high")),
                "low": _nasdaq_dollar(r.get("low")),
                "close": _nasdaq_dollar(r.get("close")),
                "volume": _nasdaq_int(r.get("volume")),
            }
        )
    out.sort(key=lambda r: r["date"], reverse=True)
    return out


# ---------- Yahoo Finance (chart endpoint) ----------
#
# Why chart not v7/quote: the v7 batched quote endpoint requires a crumb token
# that has to be scraped from a browser-rendered page; the v8 chart endpoint
# is unauthenticated and serves one symbol per call. Trade-off: no batching
# from Yahoo. We loop over symbols.
#
# Known issue: Yahoo throttles aggressively by source IP (HTTP 429 for the
# whole IP range when one tenant abuses it). Treat 429 as a soft failure and
# let the fallback chain continue.


def _yh_symbol_from_secid(secid: str) -> str | None:
    """Map an Eastmoney secid (e.g. '116.00700') to a Yahoo symbol (e.g. '0700.HK')."""
    parts = secid.split(".", 1)
    if len(parts) != 2:
        return None
    prefix, code = parts
    suffix = YH_EM_PREFIX_TO_SUFFIX.get(prefix)
    if suffix is None:
        return None
    if prefix == "116":
        # HK Yahoo strips a leading zero: 00700 → 0700.HK
        code = code.lstrip("0") or "0"
        if len(code) < 4:
            code = code.zfill(4)
    return f"{code}{suffix}"


def _yh_symbol_from_index_alias(alias_key: str) -> str | None:
    return YH_INDEX_FROM_ALIAS.get(alias_key.upper().replace(" ", "").replace("_", ""))


def yh_chart_raw(yh_symbol: str, *, interval: str = "1d", range_: str = "5d") -> dict[str, Any] | None:
    """Hit Yahoo's chart endpoint; return parsed JSON or None on failure."""
    qs = urllib.parse.urlencode({"interval": interval, "range": range_})
    url = f"{YH_CHART}/{urllib.parse.quote(yh_symbol, safe='')}?{qs}"
    try:
        j = http_json(url)
    except Exception:
        return None
    chart = (j or {}).get("chart") or {}
    if chart.get("error"):
        return None
    result = (chart.get("result") or [None])[0]
    return result


def yh_quote_one(yh_symbol: str) -> dict[str, Any] | None:
    r = yh_chart_raw(yh_symbol, interval="1d", range_="5d")
    if not r:
        return None
    meta = r.get("meta") or {}
    last = meta.get("regularMarketPrice")
    prev = meta.get("chartPreviousClose") or meta.get("previousClose")
    change = None
    pct = None
    if last is not None and prev:
        change = round(last - prev, 4)
        pct = round((last - prev) / prev * 100, 4)
    return {
        "symbol": meta.get("symbol"),
        "name": meta.get("longName") or meta.get("shortName"),
        "exchange": meta.get("exchangeName"),
        "price": last,
        "open": meta.get("regularMarketDayHigh"),  # meta lacks open in some series; intentional fallback
        "high": meta.get("regularMarketDayHigh"),
        "low": meta.get("regularMarketDayLow"),
        "prev_close": prev,
        "change": change,
        "pct": pct,
        "volume": meta.get("regularMarketVolume"),
        "currency": meta.get("currency"),
        "source": "yahoo",
    }


def yh_history(yh_symbol: str, from_d: date, to_d: date) -> list[dict[str, Any]] | None:
    span_days = max((to_d - from_d).days + 1, 1)
    # Pick the smallest range that covers the request; Yahoo's range= is preferred
    # over period1/period2 to avoid epoch/timezone subtleties.
    if span_days <= 5:
        range_ = "5d"
    elif span_days <= 30:
        range_ = "1mo"
    elif span_days <= 90:
        range_ = "3mo"
    elif span_days <= 180:
        range_ = "6mo"
    elif span_days <= 365:
        range_ = "1y"
    elif span_days <= 730:
        range_ = "2y"
    else:
        range_ = "5y"
    r = yh_chart_raw(yh_symbol, interval="1d", range_=range_)
    if not r:
        return None
    ts = r.get("timestamp") or []
    quote = ((r.get("indicators") or {}).get("quote") or [{}])[0]
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    vols = quote.get("volume") or []
    rows: list[dict[str, Any]] = []
    fr = from_d.strftime("%Y-%m-%d")
    to = to_d.strftime("%Y-%m-%d")
    for i, t in enumerate(ts):
        d_str = datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")
        if d_str < fr or d_str > to:
            continue
        if i >= len(closes) or closes[i] is None:
            continue
        rows.append({
            "date": d_str,
            "open": opens[i] if i < len(opens) else None,
            "high": highs[i] if i < len(highs) else None,
            "low": lows[i] if i < len(lows) else None,
            "close": closes[i],
            "volume": vols[i] if i < len(vols) else None,
        })
    rows.sort(key=lambda r: r["date"], reverse=True)
    return rows


def yh_fx_latest(base: str, targets: list[str]) -> dict[str, Any] | None:
    """Yahoo FX via chart endpoint. One symbol per call (no batch)."""
    out_rates: dict[str, float] = {}
    asof_date: str | None = None
    for t in targets:
        sym = f"{base.upper()}{t.upper()}=X"
        r = yh_chart_raw(sym, interval="1d", range_="5d")
        if not r:
            continue
        meta = r.get("meta") or {}
        price = meta.get("regularMarketPrice")
        if price is None:
            continue
        out_rates[t.upper()] = price
        ts = meta.get("regularMarketTime")
        if ts and not asof_date:
            asof_date = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
    if not out_rates:
        return None
    return {
        "amount": 1.0,
        "base": base.upper(),
        "date": asof_date or date.today().isoformat(),
        "rates": out_rates,
        "source": "yahoo",
    }





def fx_latest(base: str, targets: list[str]) -> dict[str, Any]:
    qs = urllib.parse.urlencode({"base": base.upper(), "symbols": ",".join(t.upper() for t in targets)})
    try:
        r = http_json(f"{FX_BASE}/latest?{qs}")
        r["source"] = "frankfurter"
        return r
    except Exception as e:
        y = yh_fx_latest(base, targets)
        if y:
            y["fallback_reason"] = str(e)
            return y
        raise


def fx_history(base: str, target: str, from_d: date, to_d: date) -> dict[str, Any]:
    qs = urllib.parse.urlencode({"base": base.upper(), "symbols": target.upper()})
    url = f"{FX_BASE}/{from_d.isoformat()}..{to_d.isoformat()}?{qs}"
    return http_json(url)


# ---------- Dispatch ----------


def is_secid(s: str) -> bool:
    parts = s.split(".")
    return len(parts) == 2 and parts[0].isdigit()


def resolve_index(name: str) -> str:
    key = name.upper().replace(" ", "").replace("_", "")
    if key in INDEX_ALIASES:
        return INDEX_ALIASES[key]
    if is_secid(name):
        return name
    die(f"unknown index '{name}'. Supported: {', '.join(sorted(set(INDEX_ALIASES.values())))}")


def cmd_quote(args: argparse.Namespace) -> Any:
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    source = args.source
    out = []
    for sym in symbols:
        chosen = source or ("eastmoney" if is_secid(sym) else "nasdaq")
        if chosen == "eastmoney":
            out.append(em_quote_one(sym))
        elif chosen == "yahoo":
            yh_sym = _yh_symbol_from_secid(sym) if is_secid(sym) else sym
            r = yh_quote_one(yh_sym) or {"symbol": sym, "error": "yahoo no data"}
            out.append(r)
        else:
            out.append(nasdaq_quote_one(sym))
    return out


def cmd_index(args: argparse.Namespace) -> Any:
    names = [n.strip() for n in args.names.split(",") if n.strip()]
    out = []
    for n in names:
        secid = resolve_index(n)
        try:
            row = em_quote_one(secid)
        except (urllib.error.URLError, OSError) as e:
            row = {"symbol": n, "secid": secid, "error": str(e)}
        # em_quote_one already auto-falls-back via _yh_symbol_from_secid, but
        # `100.*` indices don't have a secid→yahoo mapping. Add a per-alias try.
        if row.get("error") or row.get("price") is None:
            yh_sym = _yh_symbol_from_index_alias(n)
            if yh_sym:
                y = yh_quote_one(yh_sym)
                if y:
                    y["secid"] = secid
                    y["fallback_reason"] = row.get("error", "no eastmoney data")
                    row = y
        out.append(row)
    return out


def cmd_history(args: argparse.Namespace) -> Any:
    fr, to = resolve_range(args)
    sym = args.symbol
    source = args.source or ("eastmoney" if is_secid(sym) else "nasdaq")
    if source == "eastmoney":
        return em_history(sym, fr, to)
    if source == "yahoo":
        yh_sym = _yh_symbol_from_secid(sym) if is_secid(sym) else sym
        r = yh_history(yh_sym, fr, to)
        return r if r is not None else []
    return nasdaq_history(sym, fr, to)


def cmd_search(args: argparse.Namespace) -> Any:
    return em_search(args.query, args.limit)


def cmd_fx(args: argparse.Namespace) -> Any:
    targets = [t.strip() for t in args.to.split(",") if t.strip()]
    return fx_latest(args.from_ccy, targets)


def cmd_fx_history(args: argparse.Namespace) -> Any:
    fr, to = resolve_range(args)
    return fx_history(args.from_ccy, args.to, fr, to)


def main(argv: list[str]) -> None:
    p = argparse.ArgumentParser(prog="equity", description="global equities + FX")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_range_flags(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--from", dest="from_date", help="YYYY-MM-DD")
        sp.add_argument("--to", dest="to_date", help="YYYY-MM-DD")
        sp.add_argument("--days", type=int, help="last N calendar days")

    q = sub.add_parser("quote", help="last price for one or more symbols")
    q.add_argument("symbols", help="ticker or comma-separated tickers/secids")
    q.add_argument("--source", choices=["nasdaq", "eastmoney", "yahoo"])
    q.set_defaults(func=cmd_quote)

    idx = sub.add_parser("index", help="major index quote")
    idx.add_argument("names", help="index name(s): SPX, NDX, DJI, HSI, DAX")
    idx.set_defaults(func=cmd_index)

    h = sub.add_parser("history", help="daily OHLCV history")
    h.add_argument("symbol")
    h.add_argument("--source", choices=["nasdaq", "eastmoney", "yahoo"])
    add_range_flags(h)
    h.set_defaults(func=cmd_history)

    s = sub.add_parser("search", help="search for ticker by name")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=10)
    s.set_defaults(func=cmd_search)

    fx = sub.add_parser("fx", help="latest FX rate")
    fx.add_argument("from_ccy", metavar="FROM", help="base currency, e.g. USD")
    fx.add_argument("to", help="target currency or comma list, e.g. EUR,JPY")
    fx.set_defaults(func=cmd_fx)

    fxh = sub.add_parser("fx-history", help="historical FX series")
    fxh.add_argument("from_ccy", metavar="FROM")
    fxh.add_argument("to", metavar="TO")
    add_range_flags(fxh)
    fxh.set_defaults(func=cmd_fx_history)

    args = p.parse_args(argv)
    try:
        result = args.func(args)
    except (urllib.error.URLError, OSError) as e:
        die(f"network error: {e}")
    except json.JSONDecodeError as e:
        die(f"upstream returned non-JSON: {e}")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
