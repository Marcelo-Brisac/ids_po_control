#!/usr/bin/env python3
"""macro-rates-fx / fx: FX latest + historical from ECB reference rates
via api.frankfurter.dev. Keyless, stdlib only.

Subcommands:
  latest FROM TO[,TO,...]                  latest snapshot for one base → many quote currencies
  history FROM TO --from --to              daily series for one pair
  convert AMOUNT FROM TO                   convert at latest rate
  symbols                                  list supported currencies

Output: JSON to stdout. Errors: JSON {"error": "..."} with exit code 1.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from typing import Any, NoReturn

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
TIMEOUT = 12
BASE = "https://api.frankfurter.dev/v1"


def die(msg: str, code: int = 1) -> NoReturn:
    print(json.dumps({"error": msg}, ensure_ascii=False))
    sys.exit(code)


def _get_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def cmd_latest(args):
    qs = urllib.parse.urlencode({"base": args.fr.upper(), "symbols": args.to.upper()})
    return _get_json(f"{BASE}/latest?{qs}")


def cmd_history(args):
    end = args.end or date.today().isoformat()
    start = args.start or (date.fromisoformat(end) - timedelta(days=365)).isoformat()
    qs = urllib.parse.urlencode({"base": args.fr.upper(), "symbols": args.to.upper()})
    return _get_json(f"{BASE}/{start}..{end}?{qs}")


def cmd_convert(args):
    qs = urllib.parse.urlencode({"base": args.fr.upper(), "symbols": args.to.upper()})
    j = _get_json(f"{BASE}/latest?{qs}")
    rate = j["rates"].get(args.to.upper())
    if rate is None:
        return {"error": f"no rate {args.fr}→{args.to}"}
    return {
        "amount": args.amount,
        "from": args.fr.upper(),
        "to": args.to.upper(),
        "rate": rate,
        "date": j.get("date"),
        "result": args.amount * rate,
    }


def cmd_symbols(args):
    return _get_json(f"{BASE}/currencies")


def main() -> None:
    p = argparse.ArgumentParser(prog="fx.py", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("latest", help="latest FX snapshot")
    pl.add_argument("fr", metavar="FROM")
    pl.add_argument("to", metavar="TO", help="comma-separated target currencies (e.g. EUR,JPY,GBP)")
    pl.set_defaults(func=cmd_latest)

    ph = sub.add_parser("history", help="daily series for one pair (or one base → many)")
    ph.add_argument("fr", metavar="FROM")
    ph.add_argument("to", metavar="TO")
    ph.add_argument("--from", dest="start", help="YYYY-MM-DD; default = 1y ago")
    ph.add_argument("--to", dest="end", help="YYYY-MM-DD; default = today")
    ph.set_defaults(func=cmd_history)

    pc = sub.add_parser("convert", help="convert AMOUNT at latest rate")
    pc.add_argument("amount", type=float)
    pc.add_argument("fr", metavar="FROM")
    pc.add_argument("to", metavar="TO")
    pc.set_defaults(func=cmd_convert)

    sub.add_parser("symbols", help="list supported currencies").set_defaults(func=cmd_symbols)

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
