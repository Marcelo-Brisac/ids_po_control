#!/usr/bin/env python3
"""macro-rates-fx / rates: US Treasury yields and yield curve.

Provider: Treasury Direct (home.treasury.gov) — daily CSV, keyless.
Stdlib only.

Subcommands:
  curve [--date YYYY-MM-DD]       full yield curve for one date (default: most recent)
  series TENOR [--from --to]      single-tenor history (tenors: 1M, 1.5M, 2M, 3M, 4M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y)
  recent [--days N]               recent rows of the full curve (default 30)

Output: JSON to stdout. Errors: JSON {"error": "..."} with exit code 1.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import urllib.error
import urllib.request
from datetime import date, datetime
from typing import Any, NoReturn

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
TIMEOUT = 15
TREASURY_CSV = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "daily-treasury-rates.csv/all/{yearmonth}?type=daily_treasury_yield_curve&field_tdr_date_value_month={yearmonth}"
)
# Header tenor → canonical key
TENOR_MAP = {
    "1 Mo": "1M", "1.5 Month": "1.5M", "2 Mo": "2M", "3 Mo": "3M",
    "4 Mo": "4M", "6 Mo": "6M", "1 Yr": "1Y", "2 Yr": "2Y", "3 Yr": "3Y",
    "5 Yr": "5Y", "7 Yr": "7Y", "10 Yr": "10Y", "20 Yr": "20Y", "30 Yr": "30Y",
}


def die(msg: str, code: int = 1) -> NoReturn:
    print(json.dumps({"error": msg}, ensure_ascii=False))
    sys.exit(code)


def _fetch_month(yearmonth: str) -> list[dict[str, Any]]:
    url = TREASURY_CSV.format(yearmonth=yearmonth)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        text = resp.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    out = []
    for row in reader:
        d = datetime.strptime(row["Date"], "%m/%d/%Y").date()
        rec: dict[str, Any] = {"date": d.isoformat()}
        for raw, key in TENOR_MAP.items():
            v = row.get(raw, "").strip()
            rec[key] = float(v) if v else None
        out.append(rec)
    return out


def _fetch_range(start: date, end: date) -> list[dict[str, Any]]:
    """Iterate by month, dedup, return sorted desc by date."""
    seen = {}
    cur = date(start.year, start.month, 1)
    while cur <= end:
        ym = f"{cur.year:04d}{cur.month:02d}"
        try:
            for row in _fetch_month(ym):
                if start.isoformat() <= row["date"] <= end.isoformat():
                    seen[row["date"]] = row
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
        # next month
        if cur.month == 12:
            cur = date(cur.year + 1, 1, 1)
        else:
            cur = date(cur.year, cur.month + 1, 1)
    return sorted(seen.values(), key=lambda r: r["date"], reverse=True)


def cmd_curve(args):
    target = args.date or date.today().isoformat()
    target_d = date.fromisoformat(target)
    rows = _fetch_month(f"{target_d.year:04d}{target_d.month:02d}")
    if not rows:
        return {"error": "no rates for month", "date": target}
    # Most recent row on or before target
    on_or_before = [r for r in rows if r["date"] <= target]
    if not on_or_before:
        return {"error": "no rates on or before date", "date": target, "available": [r["date"] for r in rows]}
    row = max(on_or_before, key=lambda r: r["date"])
    return {"as_of": row["date"], "curve": {k: row[k] for k in TENOR_MAP.values()}, "source": "treasury_direct"}


def cmd_series(args):
    tenor = args.tenor.upper().replace(".0", "")
    if tenor not in TENOR_MAP.values():
        return {"error": f"unknown tenor {tenor!r}", "valid": list(TENOR_MAP.values())}
    end = date.fromisoformat(args.to) if args.to else date.today()
    start = date.fromisoformat(getattr(args, "from")) if getattr(args, "from") else date(end.year - 1, end.month, end.day)
    rows = _fetch_range(start, end)
    return {
        "tenor": tenor,
        "from": start.isoformat(),
        "to": end.isoformat(),
        "series": [{"date": r["date"], "rate": r[tenor]} for r in rows if r[tenor] is not None],
        "source": "treasury_direct",
    }


def cmd_recent(args):
    end = date.today()
    # Need at least args.days business days; fetch 2 months back to be safe.
    start = date(end.year - (1 if end.month <= 2 else 0), (end.month - 2) % 12 or 12, 1)
    rows = _fetch_range(start, end)[: args.days]
    return {"count": len(rows), "rows": rows, "source": "treasury_direct"}


def main() -> None:
    p = argparse.ArgumentParser(prog="rates.py", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("curve", help="full yield curve for one date")
    pc.add_argument("--date", help="YYYY-MM-DD; default = today")
    pc.set_defaults(func=cmd_curve)

    ps = sub.add_parser("series", help="single-tenor history")
    ps.add_argument("tenor", help="1M, 3M, 6M, 1Y, 2Y, 5Y, 10Y, 30Y, ...")
    ps.add_argument("--from", dest="from", help="YYYY-MM-DD")
    ps.add_argument("--to", help="YYYY-MM-DD; default = today")
    ps.set_defaults(func=cmd_series)

    pr = sub.add_parser("recent", help="recent N rows of the full curve")
    pr.add_argument("--days", type=int, default=30)
    pr.set_defaults(func=cmd_recent)

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
