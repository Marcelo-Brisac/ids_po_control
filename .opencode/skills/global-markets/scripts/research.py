#!/usr/bin/env python3
"""global-markets / research: per-name research for global listed equities.

Provider: yfinance (Yahoo Finance scraper). Lazy-imported — install only if
your workflow needs research:

    uv sync --frozen   # at skill root; then invoke via `uv run scripts/research.py …`

Subcommands cover fundamentals (income / balance sheet / cash flow), holders,
insider transactions, analyst recommendations & estimates, earnings calendar,
news, and dividends/splits history.

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
    """Lazy import yfinance with structured ImportError for the agent."""
    try:
        import yfinance as yf  # type: ignore
    except ImportError:
        die(
            "yfinance not installed",
            install="uv sync --frozen   # at skill root, then re-invoke via `uv run scripts/research.py …`",
            code=2,
        )
    return yf


# ---- Helpers ----

def _df_to_records(df) -> list[dict[str, Any]] | None:
    """Convert a pandas DataFrame to list-of-dicts with stringified column labels.

    Sanitizes NaN/NaT/pd.NA → None at the dict level (df.where(notna, None) is
    unreliable on float columns and lets bare NaN leak into JSON output).
    """
    if df is None:
        return None
    try:
        if hasattr(df, "empty") and df.empty:
            return []
    except Exception:
        pass
    try:
        import math
        import pandas as pd
        # Stringify column labels (often Timestamps for statement DFs).
        df2 = df.copy()
        df2.columns = [str(c)[:10] if hasattr(c, "strftime") else str(c) for c in df2.columns]
        # Index becomes the row label.
        df2 = df2.reset_index().rename(columns={"index": "field"})
        if "field" not in df2.columns and df2.columns[0] != "field":
            df2 = df2.rename(columns={df2.columns[0]: "field"})
        df2["field"] = df2["field"].astype(str)
        # Stringify datetime columns (preserve null as None).
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
        return None


def _series_to_records(s) -> list[dict[str, Any]] | None:
    if s is None:
        return None
    try:
        if hasattr(s, "empty") and s.empty:
            return []
    except Exception:
        pass
    try:
        out = []
        for k, v in s.items():
            key = str(k)[:10] if hasattr(k, "strftime") else str(k)
            out.append({"date": key, "value": float(v) if v == v else None})  # NaN check
        return out
    except Exception:
        return None


# ---- Commands ----


def cmd_earnings_calendar(args):
    """Upcoming/recent earnings across all US listings in a date window (Nasdaq).

    Stdlib — does NOT require yfinance. Scans one date per request; we walk
    the window and aggregate. Skips silently on per-day failures.
    """
    import urllib.error
    import urllib.request
    from datetime import date, datetime, timedelta

    UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    today = date.today()
    start = datetime.strptime(args.start, "%Y-%m-%d").date() if args.start else today
    end = datetime.strptime(args.end, "%Y-%m-%d").date() if args.end else (start + timedelta(days=14))
    if end < start:
        return {"error": "end before start"}
    if (end - start).days > 60:
        return {"error": "window > 60 days; reduce range"}

    rows: list[dict[str, Any]] = []
    skipped: list[str] = []
    d = start
    while d <= end:
        url = f"https://api.nasdaq.com/api/calendar/earnings?date={d.isoformat()}"
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "application/json, text/plain, */*",
        })
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                j = json.loads(resp.read().decode("utf-8"))
            data = (j.get("data") or {})
            entries = data.get("rows") or []
            for r in entries:
                rows.append({
                    "date": d.isoformat(),
                    "symbol": r.get("symbol"),
                    "name": r.get("name"),
                    "time": r.get("time"),
                    "fiscal_quarter_ending": r.get("fiscalQuarterEnding"),
                    "eps_forecast": r.get("epsForecast"),
                    "num_estimates": r.get("noOfEsts"),
                    "last_year_eps": r.get("lastYearEPS"),
                    "last_year_report_date": r.get("lastYearRptDt"),
                    "market_cap": r.get("marketCap"),
                })
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError) as e:
            skipped.append(f"{d.isoformat()}: {type(e).__name__}")
        d += timedelta(days=1)

    # Optional symbol filter — Nasdaq returns the full day; pare down if user asked.
    if args.symbols:
        wanted = {s.strip().upper() for s in args.symbols.split(",")}
        rows = [r for r in rows if r.get("symbol", "").upper() in wanted]

    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "count": len(rows),
        "skipped_days": skipped or None,
        "earnings": rows[: args.limit] if args.limit else rows,
        "source": "nasdaq",
    }

def cmd_fundamentals(args):
    yf = _yf()
    t = yf.Ticker(args.symbol)
    if args.quarterly:
        income = t.quarterly_income_stmt
        balance = t.quarterly_balance_sheet
        cashflow = t.quarterly_cash_flow
    else:
        income = t.income_stmt
        balance = t.balance_sheet
        cashflow = t.cash_flow
    return {
        "symbol": args.symbol.upper(),
        "period": "quarterly" if args.quarterly else "annual",
        "income_statement": _df_to_records(income),
        "balance_sheet": _df_to_records(balance),
        "cash_flow": _df_to_records(cashflow),
        "source": "yfinance",
    }


def cmd_info(args):
    yf = _yf()
    t = yf.Ticker(args.symbol)
    info = t.info or {}
    # Cherry-pick the most useful fields; full info dict is too large and noisy.
    keys = [
        "symbol", "shortName", "longName", "sector", "industry", "country",
        "currency", "exchange", "quoteType", "marketCap", "enterpriseValue",
        "sharesOutstanding", "floatShares", "heldPercentInstitutions",
        "heldPercentInsiders", "trailingPE", "forwardPE", "priceToBook",
        "priceToSalesTrailing12Months", "enterpriseToRevenue", "enterpriseToEbitda",
        "trailingEps", "forwardEps", "dividendYield", "dividendRate", "exDividendDate",
        "payoutRatio", "fiveYearAvgDividendYield", "beta", "fiftyTwoWeekHigh",
        "fiftyTwoWeekLow", "averageVolume", "averageVolume10days",
        "regularMarketPrice", "regularMarketPreviousClose",
        "returnOnAssets", "returnOnEquity", "grossMargins", "operatingMargins",
        "profitMargins", "ebitdaMargins", "revenueGrowth", "earningsGrowth",
        "totalCash", "totalDebt", "debtToEquity", "currentRatio", "quickRatio",
        "freeCashflow", "operatingCashflow", "totalRevenue", "grossProfits",
        "ebitda", "netIncomeToCommon", "trailingAnnualDividendYield",
        "longBusinessSummary",
    ]
    out = {k: info.get(k) for k in keys if k in info}
    out["source"] = "yfinance"
    return out


def cmd_holders(args):
    yf = _yf()
    t = yf.Ticker(args.symbol)
    return {
        "symbol": args.symbol.upper(),
        "major_holders": _df_to_records(t.major_holders),
        "institutional_holders": _df_to_records(t.institutional_holders),
        "mutualfund_holders": _df_to_records(t.mutualfund_holders),
        "source": "yfinance",
    }


def cmd_insiders(args):
    yf = _yf()
    t = yf.Ticker(args.symbol)
    return {
        "symbol": args.symbol.upper(),
        "transactions": _df_to_records(t.insider_transactions),
        "roster_holders": _df_to_records(t.insider_roster_holders),
        "purchases": _df_to_records(t.insider_purchases),
        "source": "yfinance",
    }


def cmd_recommendations(args):
    yf = _yf()
    t = yf.Ticker(args.symbol)
    return {
        "symbol": args.symbol.upper(),
        "recommendations": _df_to_records(t.recommendations),
        "upgrades_downgrades": _df_to_records(t.upgrades_downgrades),
        "analyst_price_targets": t.analyst_price_targets if hasattr(t, "analyst_price_targets") else None,
        "source": "yfinance",
    }


def cmd_estimates(args):
    yf = _yf()
    t = yf.Ticker(args.symbol)
    return {
        "symbol": args.symbol.upper(),
        "earnings_estimate": _df_to_records(t.earnings_estimate) if hasattr(t, "earnings_estimate") else None,
        "revenue_estimate": _df_to_records(t.revenue_estimate) if hasattr(t, "revenue_estimate") else None,
        "earnings_history": _df_to_records(t.earnings_history) if hasattr(t, "earnings_history") else None,
        "eps_trend": _df_to_records(t.eps_trend) if hasattr(t, "eps_trend") else None,
        "eps_revisions": _df_to_records(t.eps_revisions) if hasattr(t, "eps_revisions") else None,
        "growth_estimates": _df_to_records(t.growth_estimates) if hasattr(t, "growth_estimates") else None,
        "source": "yfinance",
    }


def cmd_calendar(args):
    yf = _yf()
    t = yf.Ticker(args.symbol)
    cal = t.calendar
    if cal is None:
        return {"symbol": args.symbol.upper(), "calendar": None, "source": "yfinance"}
    if isinstance(cal, dict):
        out_cal = {k: (v.isoformat() if hasattr(v, "isoformat") else (list(v) if hasattr(v, "__iter__") and not isinstance(v, str) else v)) for k, v in cal.items()}
    else:
        out_cal = _df_to_records(cal)
    return {"symbol": args.symbol.upper(), "calendar": out_cal, "source": "yfinance"}


def cmd_news(args):
    yf = _yf()
    t = yf.Ticker(args.symbol)
    items = t.news or []
    out = []
    for it in items[: args.limit]:
        # yfinance returns either flat dict or {"content": {...}} (v0.2.40+).
        c = it.get("content", it) if isinstance(it, dict) else {}
        out.append({
            "title": c.get("title") or it.get("title"),
            "summary": c.get("summary") or it.get("summary"),
            "publisher": (c.get("provider") or {}).get("displayName") if isinstance(c.get("provider"), dict) else c.get("publisher") or it.get("publisher"),
            "pubDate": c.get("pubDate") or it.get("providerPublishTime"),
            "url": (c.get("canonicalUrl") or {}).get("url") if isinstance(c.get("canonicalUrl"), dict) else c.get("link") or it.get("link"),
            "type": c.get("contentType") or it.get("type"),
        })
    return {"symbol": args.symbol.upper(), "count": len(out), "news": out, "source": "yfinance"}


def cmd_actions(args):
    """Dividends + splits + (optional) capital gains history."""
    yf = _yf()
    t = yf.Ticker(args.symbol)
    out: dict[str, Any] = {"symbol": args.symbol.upper(), "source": "yfinance"}
    out["dividends"] = _series_to_records(t.dividends)
    out["splits"] = _series_to_records(t.splits)
    try:
        out["capital_gains"] = _series_to_records(t.capital_gains)
    except Exception:
        out["capital_gains"] = None
    return out


def cmd_sustainability(args):
    yf = _yf()
    t = yf.Ticker(args.symbol)
    return {
        "symbol": args.symbol.upper(),
        "sustainability": _df_to_records(t.sustainability),
        "source": "yfinance",
    }


def main() -> None:
    p = argparse.ArgumentParser(prog="research.py", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name: str, help_: str, func, *extra):
        sp = sub.add_parser(name, help=help_)
        sp.add_argument("symbol", help="ticker symbol (e.g. AAPL, 0700.HK, 7203.T)")
        for fn in extra:
            fn(sp)
        sp.set_defaults(func=func)
        return sp

    add("fundamentals", "income statement + balance sheet + cash flow",
        cmd_fundamentals,
        lambda sp: sp.add_argument("--quarterly", action="store_true", help="quarterly periods (default: annual)"))
    add("info", "company snapshot — sector/industry, ratios, share counts, margins, summary", cmd_info)
    add("holders", "major / institutional / mutual fund holders", cmd_holders)
    add("insiders", "insider transactions + roster + recent purchases", cmd_insiders)
    add("recommendations", "analyst recommendations + upgrades/downgrades + price targets", cmd_recommendations)
    add("estimates", "earnings + revenue estimates, EPS trend + revisions, growth estimates", cmd_estimates)
    add("calendar", "upcoming earnings/dividend dates + EPS estimate", cmd_calendar)
    add("news", "Yahoo Finance news headlines for the symbol",
        cmd_news,
        lambda sp: sp.add_argument("--limit", type=int, default=20))
    add("actions", "dividend + split history (+ capital gains for funds)", cmd_actions)
    add("sustainability", "ESG / sustainability scores", cmd_sustainability)

    # earnings-calendar is window-based (no symbol positional, stdlib only).
    pec = sub.add_parser("earnings-calendar",
                         help="upcoming/recent US earnings in a date window (Nasdaq, stdlib)")
    pec.add_argument("--start", help="YYYY-MM-DD; default = today")
    pec.add_argument("--end", help="YYYY-MM-DD; default = start + 14 days")
    pec.add_argument("--symbols", help="filter to comma-separated tickers (case-insensitive)")
    pec.add_argument("--limit", type=int, default=0, help="cap output rows (0 = all)")
    pec.set_defaults(func=cmd_earnings_calendar)

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
