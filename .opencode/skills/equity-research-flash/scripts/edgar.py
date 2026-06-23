#!/usr/bin/env python3
"""equity-research: thin SEC EDGAR fetch primitive.

EDGAR returns 403 to bare HTTP clients; it requires a User-Agent
identifying the requester (SEC policy). This script is the minimum
needed to get past that gate. The agent already knows form types
(10-K / 10-Q / 8-K / DEF 14A / S-1 / 13F / Form 4 / 13G / 13D), 10-K
Item structure, accession-number format, and EDGAR URL patterns
(`data.sec.gov/submissions/CIK<10>.json`, `www.sec.gov/Archives/edgar/data/<cik>/<acc-no-dashes>/<file>`).
Only the UA-gate and ticker->CIK lookup need a script.

Keyless. UA from $SEC_USER_AGENT or a default. Two commands:

  edgar.py cik <ticker>     resolve ticker to 10-digit zero-padded CIK
  edgar.py fetch <url>      GET an EDGAR URL with the right headers

Examples:
  edgar.py cik NKE
  edgar.py fetch https://data.sec.gov/submissions/CIK0000320187.json | jq '.filings.recent.form[:5]'
  edgar.py fetch https://www.sec.gov/Archives/edgar/data/320187/000032018724000142/nke-20240531.htm
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import NoReturn

UA = os.environ.get("SEC_USER_AGENT", "equity-research-skill contact@example.com")
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# data.sec.gov needs Host header; www.sec.gov is fine without explicit Host.
def _get(url: str) -> tuple[str, str]:
    """GET url with EDGAR-compliant headers. Returns (body, content_type)."""
    parsed = urllib.parse.urlparse(url)
    headers = {
        "User-Agent": UA,
        "Accept-Encoding": "gzip, deflate",
        "Host": parsed.netloc,
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            ctype = r.headers.get("Content-Type", "")
            raw = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                import gzip
                raw = gzip.decompress(raw)
            elif r.headers.get("Content-Encoding") == "deflate":
                import zlib
                raw = zlib.decompress(raw)
            return raw.decode("utf-8", errors="replace"), ctype
    except urllib.error.HTTPError as e:
        die(f"HTTP {e.code} {e.reason} for {url}")


def die(msg: str) -> NoReturn:
    sys.stderr.write(f"edgar: {msg}\n")
    sys.exit(1)


def cmd_cik(args: argparse.Namespace) -> None:
    body, _ = _get(TICKERS_URL)
    data = json.loads(body)
    target = args.ticker.upper()
    for _, row in data.items():
        if row.get("ticker", "").upper() == target:
            cik = str(row["cik_str"]).zfill(10)
            print(cik)
            return
    die(f"ticker not found: {target}")


def cmd_fetch(args: argparse.Namespace) -> None:
    body, ctype = _get(args.url)
    if "json" in ctype.lower():
        try:
            print(json.dumps(json.loads(body), indent=2, ensure_ascii=False))
            return
        except json.JSONDecodeError:
            pass
    sys.stdout.write(body)


def main() -> None:
    p = argparse.ArgumentParser(prog="edgar", description="Thin SEC EDGAR fetch primitive.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("cik", help="resolve ticker to 10-digit zero-padded CIK")
    pc.add_argument("ticker")
    pc.set_defaults(func=cmd_cik)

    pf = sub.add_parser("fetch", help="GET an EDGAR URL with the right headers")
    pf.add_argument("url")
    pf.set_defaults(func=cmd_fetch)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
