#!/usr/bin/env python3
"""crypto-markets / news: crypto-news aggregation across RSS feeds.

Uses `feedparser` (lazy-imported — install with `uv sync` at skill root,
or `pip install feedparser`).

Feeds aggregated (keyless, no signup):
  - CoinDesk           https://www.coindesk.com/arc/outboundfeeds/rss
  - CoinTelegraph      https://cointelegraph.com/rss
  - Decrypt            https://decrypt.co/feed
  - Bitcoin Magazine   https://bitcoinmagazine.com/feed
  - The Block          https://www.theblock.co/rss.xml

Use `--feeds` to restrict (comma-separated names). Use `latest` for the
most-recent N across all feeds; `feed NAME` for a single feed.

Output: JSON to stdout. Errors: JSON {"error": "..."} with exit code 1.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, NoReturn

FEEDS = {
    "coindesk":       "https://www.coindesk.com/arc/outboundfeeds/rss",
    "cointelegraph":  "https://cointelegraph.com/rss",
    "decrypt":        "https://decrypt.co/feed",
    "bitcoinmagazine":"https://bitcoinmagazine.com/feed",
    "theblock":       "https://www.theblock.co/rss.xml",
}


def die(msg: str, *, install: str | None = None, code: int = 1) -> NoReturn:
    payload: dict[str, Any] = {"error": msg}
    if install:
        payload["install"] = install
    print(json.dumps(payload, ensure_ascii=False))
    sys.exit(code)


def _fp():
    try:
        import feedparser  # type: ignore
    except ImportError:
        die("feedparser not installed", install="pip install feedparser>=6.0,<7", code=2)
    return feedparser


def _entry(e, source: str) -> dict[str, Any]:
    return {
        "title": getattr(e, "title", None),
        "url": getattr(e, "link", None),
        "summary": (getattr(e, "summary", None) or "")[:400] or None,
        "published": getattr(e, "published", None) or getattr(e, "updated", None),
        "author": getattr(e, "author", None),
        "source": source,
    }


def _resolve(names: list[str] | None) -> dict[str, str]:
    if not names:
        return FEEDS
    out = {}
    for n in names:
        n = n.strip().lower()
        if n not in FEEDS:
            die(f"unknown feed {n!r}; valid: {list(FEEDS)}")
        out[n] = FEEDS[n]
    return out


def cmd_feeds(args):
    return {"feeds": list(FEEDS.keys()), "urls": FEEDS}


def cmd_latest(args):
    """Latest N items across all (or a subset of) feeds, merged + sorted desc."""
    fp = _fp()
    feeds = _resolve(args.feeds.split(",") if args.feeds else None)
    items: list[dict[str, Any]] = []
    skipped: dict[str, str] = {}
    for name, url in feeds.items():
        try:
            d = fp.parse(url)
            if getattr(d, "bozo", 0) and not d.entries:
                skipped[name] = "parse failed"
                continue
            for e in d.entries[: args.per_feed]:
                items.append(_entry(e, name))
        except Exception as ex:
            skipped[name] = f"{type(ex).__name__}: {ex}"

    # Sort by published_parsed when available, else leave original order.
    def _ts(it):
        p = it.get("published")
        if not p:
            return 0
        # feedparser keeps published_parsed too; re-fetch from string is fragile, so
        # just sort by string lexically as a best-effort. Most RSS uses RFC822 which
        # doesn't sort lexically; we use _parsed timestamps when present.
        return 0
    # Use feedparser's struct_time if present — refetch per-feed lookup is heavier
    # than re-parsing the published field with email.utils.
    from email.utils import parsedate_to_datetime
    def _ts2(it):
        p = it.get("published")
        if not p:
            return 0
        try:
            return parsedate_to_datetime(p).timestamp()
        except Exception:
            return 0
    items.sort(key=_ts2, reverse=True)
    items = items[: args.limit]
    return {
        "count": len(items),
        "feeds_used": list(feeds.keys()),
        "skipped": skipped or None,
        "items": items,
    }


def cmd_feed(args):
    """Latest entries from one feed."""
    if args.name not in FEEDS:
        return {"error": f"unknown feed {args.name!r}", "valid": list(FEEDS)}
    fp = _fp()
    d = fp.parse(FEEDS[args.name])
    items = [_entry(e, args.name) for e in d.entries[: args.limit]]
    return {"feed": args.name, "count": len(items), "items": items}


def cmd_search(args):
    """Naive substring search across recent items from all feeds."""
    fp = _fp()
    q = args.query.lower()
    feeds = _resolve(args.feeds.split(",") if args.feeds else None)
    hits = []
    for name, url in feeds.items():
        try:
            d = fp.parse(url)
            for e in d.entries[: args.per_feed]:
                hay = " ".join(filter(None, [
                    getattr(e, "title", ""), getattr(e, "summary", ""), getattr(e, "author", "")
                ])).lower()
                if q in hay:
                    hits.append(_entry(e, name))
        except Exception:
            continue
    return {"query": args.query, "count": len(hits), "items": hits[: args.limit]}


def main() -> None:
    p = argparse.ArgumentParser(prog="news.py", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("feeds", help="list available feed names + URLs (no install needed)").set_defaults(func=cmd_feeds)

    pl = sub.add_parser("latest", help="latest items across all feeds, merged + sorted by date")
    pl.add_argument("--limit", type=int, default=30, help="total items returned")
    pl.add_argument("--per-feed", type=int, default=10, help="items pulled from each feed before merging")
    pl.add_argument("--feeds", help="comma-separated feed names (default: all)")
    pl.set_defaults(func=cmd_latest)

    pf = sub.add_parser("feed", help="latest entries from one named feed")
    pf.add_argument("name", help=f"one of: {list(FEEDS)}")
    pf.add_argument("--limit", type=int, default=20)
    pf.set_defaults(func=cmd_feed)

    ps = sub.add_parser("search", help="substring search across recent items")
    ps.add_argument("query")
    ps.add_argument("--limit", type=int, default=20)
    ps.add_argument("--per-feed", type=int, default=30)
    ps.add_argument("--feeds", help="comma-separated feed names (default: all)")
    ps.set_defaults(func=cmd_search)

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
