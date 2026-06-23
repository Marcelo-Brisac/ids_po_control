#!/usr/bin/env python3
"""macro-rates-fx / series: FRED economic series (Federal Reserve Bank of
St. Louis). US CPI, NFP, unemployment, industrial production, retail sales,
M2, etc.

Requires FRED_API_KEY environment variable. Get one (free) at
https://fred.stlouisfed.org/docs/api/api_key.html.

Subcommands:
  series ID [--from --to]      one series time-history (e.g. CPIAUCSL, UNRATE, PAYEMS)
  latest ID                    latest observation of one series
  release ID                   release schedule + most recent release date for one series
  catalogue                    print common series IDs and what they are

Output: JSON to stdout. Errors: JSON {"error": "..."} with exit code 1.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from typing import Any, NoReturn

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
TIMEOUT = 15
BASE = "https://api.stlouisfed.org/fred"

# Common series — keep small; full catalogue at https://fred.stlouisfed.org/tags/series
CATALOGUE = {
    # Inflation
    "CPIAUCSL": "CPI for All Urban Consumers (SA, level)",
    "CPILFESL": "Core CPI (ex food & energy, SA)",
    "CPIAUCNS": "CPI for All Urban Consumers (NSA)",
    "PCEPI": "PCE Price Index (Fed's preferred inflation gauge)",
    "PCEPILFE": "Core PCE Price Index",
    "PPIACO": "Producer Price Index — All Commodities",
    # Labor
    "UNRATE": "Civilian Unemployment Rate (SA)",
    "PAYEMS": "Total Nonfarm Payrolls (SA)",
    "ICSA": "Initial Jobless Claims (weekly, SA)",
    "AHETPI": "Average Hourly Earnings (production workers)",
    "CIVPART": "Labor Force Participation Rate",
    # Activity
    "GDP": "Gross Domestic Product (level, billions $)",
    "GDPC1": "Real GDP (chained 2017 $)",
    "INDPRO": "Industrial Production Index",
    "RSAFS": "Retail Sales — Advance Monthly (SA)",
    "HOUST": "Housing Starts",
    "DGORDER": "Durable Goods Orders",
    # Money / liquidity
    "M2SL": "M2 Money Stock (SA, billions $)",
    "WALCL": "Federal Reserve Total Assets",
    "DFF": "Federal Funds Effective Rate (daily)",
    "FEDFUNDS": "Federal Funds Rate (monthly)",
    # Yields
    "DGS10": "10-Year Treasury Constant Maturity Rate (daily)",
    "DGS2": "2-Year Treasury Constant Maturity Rate (daily)",
    "T10Y2Y": "10Y - 2Y Treasury Spread (daily)",
    "T10Y3M": "10Y - 3M Treasury Spread (daily, recession indicator)",
    # FX / Dollar
    "DTWEXBGS": "Trade-Weighted Dollar Index — Broad",
    "DEXUSEU": "USD/EUR Spot",
    "DEXJPUS": "JPY/USD Spot",
    # Risk / spreads
    "BAMLH0A0HYM2": "ICE BofA US High Yield OAS",
    "BAMLC0A0CM": "ICE BofA US Corporate OAS",
    "VIXCLS": "CBOE VIX (close)",
    # Sentiment
    "UMCSENT": "U Mich Consumer Sentiment",
}


def die(msg: str, code: int = 1) -> NoReturn:
    print(json.dumps({"error": msg}, ensure_ascii=False))
    sys.exit(code)


def _key() -> str:
    k = os.environ.get("FRED_API_KEY")
    if not k:
        die("FRED_API_KEY not set. Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html")
    return k


def _get_json(path: str, params: dict[str, str]) -> Any:
    params["api_key"] = _key()
    params["file_type"] = "json"
    url = f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def cmd_series(args):
    p = {"series_id": args.id.upper()}
    if getattr(args, "from"):
        p["observation_start"] = getattr(args, "from")
    if args.to:
        p["observation_end"] = args.to
    j = _get_json("series/observations", p)
    obs = j.get("observations", [])
    return {
        "id": args.id.upper(),
        "count": len(obs),
        "series": [
            {"date": o["date"], "value": float(o["value"]) if o["value"] not in ("", ".") else None}
            for o in obs
        ],
        "source": "fred",
    }


def cmd_latest(args):
    j = _get_json("series/observations", {
        "series_id": args.id.upper(),
        "sort_order": "desc",
        "limit": "1",
    })
    obs = j.get("observations", [])
    if not obs:
        return {"id": args.id.upper(), "error": "no observations"}
    o = obs[0]
    meta = _get_json("series", {"series_id": args.id.upper()})
    info = (meta.get("seriess") or [{}])[0]
    return {
        "id": args.id.upper(),
        "title": info.get("title"),
        "units": info.get("units"),
        "frequency": info.get("frequency"),
        "seasonal_adjustment": info.get("seasonal_adjustment"),
        "date": o["date"],
        "value": float(o["value"]) if o["value"] not in ("", ".") else None,
        "source": "fred",
    }


def cmd_release(args):
    rel = _get_json("series/release", {"series_id": args.id.upper()})
    info = (rel.get("releases") or [{}])[0]
    dates = _get_json("release/dates", {"release_id": str(info.get("id")), "limit": "5", "sort_order": "desc"})
    return {
        "id": args.id.upper(),
        "release": info,
        "recent_release_dates": [d["date"] for d in dates.get("release_dates", [])],
        "source": "fred",
    }


def cmd_catalogue(args):
    return CATALOGUE


def main() -> None:
    p = argparse.ArgumentParser(prog="series.py", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("series", help="time-history of one series")
    ps.add_argument("id", help="FRED series id (e.g. CPIAUCSL, UNRATE, PAYEMS)")
    ps.add_argument("--from", dest="from", help="YYYY-MM-DD")
    ps.add_argument("--to", help="YYYY-MM-DD")
    ps.set_defaults(func=cmd_series)

    pl = sub.add_parser("latest", help="latest single observation")
    pl.add_argument("id")
    pl.set_defaults(func=cmd_latest)

    pr = sub.add_parser("release", help="release calendar for a series")
    pr.add_argument("id")
    pr.set_defaults(func=cmd_release)

    sub.add_parser("catalogue", help="common series IDs and what they are").set_defaults(func=cmd_catalogue)

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
