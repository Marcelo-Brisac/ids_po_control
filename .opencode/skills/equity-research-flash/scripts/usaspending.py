#!/usr/bin/env python3
"""equity-research: thin USAspending.gov fetch primitive.

Federal-contract data for US-listed names with material government
revenue (defense primes, govtech, healthcare-public-payor). The API
is keyless and not UA-gated; this script exists to wrap the POST
body construction for the most-used query — recent contract awards
to a recipient — so the agent can pull data with one line.

For anything beyond `awards <recipient>`, the agent can hit
https://api.usaspending.gov/api/v2/ directly (no UA gate); see the
USAspending API docs for the full endpoint surface.

Examples:
  usaspending awards "LOCKHEED MARTIN"
  usaspending awards "PALANTIR" --since 2025-01-01 --limit 25
  usaspending awards "HUMANA" --type grants
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta
from typing import NoReturn

API = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

# Award type code groups. Default is contracts only — the equity-research case.
TYPE_GROUPS = {
    "contracts": ["A", "B", "C", "D"],
    "grants": ["02", "03", "04", "05"],
    "loans": ["07", "08"],
    "direct": ["06", "10", "11"],
}


def die(msg: str) -> NoReturn:
    sys.stderr.write(f"usaspending: {msg}\n")
    sys.exit(1)


def _post(body: dict) -> dict:
    req = urllib.request.Request(
        API,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "equity-research-skill contact@example.com",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        die(f"HTTP {e.code} {e.reason}: {e.read().decode('utf-8', 'replace')[:500]}")


def cmd_awards(args: argparse.Namespace) -> None:
    since = args.since or (date.today() - timedelta(days=730)).isoformat()
    until = args.until or date.today().isoformat()
    body = {
        "filters": {
            "recipient_search_text": [args.recipient.upper()],
            "time_period": [{"start_date": since, "end_date": until}],
            "award_type_codes": TYPE_GROUPS[args.type],
        },
        "fields": [
            "Award ID",
            "Recipient Name",
            "Award Amount",
            "Awarding Agency",
            "Awarding Sub Agency",
            "Description",
            "Period of Performance Start Date",
            "Period of Performance Current End Date",
        ],
        "sort": "Award Amount",
        "order": "desc",
        "limit": args.limit,
        "page": 1,
    }
    print(json.dumps(_post(body), indent=2, ensure_ascii=False))


def main() -> None:
    p = argparse.ArgumentParser(prog="usaspending", description="Thin USAspending.gov fetch primitive.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("awards", help="recent federal awards for a recipient (substring match)")
    pa.add_argument("recipient", help="recipient name substring, e.g. 'LOCKHEED MARTIN'")
    pa.add_argument("--since", help="start date YYYY-MM-DD (default: 2 years ago)")
    pa.add_argument("--until", help="end date YYYY-MM-DD (default: today)")
    pa.add_argument("--limit", type=int, default=25, help="rows to return (default 25)")
    pa.add_argument(
        "--type",
        choices=list(TYPE_GROUPS.keys()),
        default="contracts",
        help="award type group (default: contracts)",
    )
    pa.set_defaults(func=cmd_awards)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
