#!/usr/bin/env python3
"""
Reddit Search Posts — search public Reddit posts by keyword.

Usage:
    python3 reddit-search.py '<json_body>'

Prints formatted summary to stdout. Saves raw JSON to /tmp/reddit_search_<pid>.json.

Body fields (see SKILL.md for full schema):
    query (required), subreddit (no "r/" prefix), sort, time, cursor.

`time` is only valid when sort="top".

Example:
    python3 reddit-search.py '{"query":"openai","subreddit":"OpenAI","sort":"top","time":"week"}'
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, NoReturn, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE_URL = os.environ.get("REDDIT_SEARCH_BASE_URL", "")
API_KEY = os.environ.get("REDDIT_SEARCH_API_KEY", "")


def die(msg: str, detail: Optional[str] = None) -> NoReturn:
    err: Dict[str, str] = {"error": msg}
    if detail:
        err["detail"] = detail
    print(json.dumps(err, indent=2), file=sys.stderr)
    sys.exit(1)


def api_call(body: Dict[str, Any]) -> tuple:
    if not BASE_URL:
        die("No base URL — set REDDIT_SEARCH_BASE_URL")
    if not API_KEY:
        die("No API key — set REDDIT_SEARCH_API_KEY")

    url = f"{BASE_URL}/v1/search-posts"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "identity",
        "Authorization": f"Bearer {API_KEY}",
    }
    req = Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")

    try:
        with urlopen(req, timeout=60) as resp:
            raw = resp.read()
            if not raw:
                die(f"Empty response (HTTP {resp.status})")
            try:
                result = json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                die(f"Invalid JSON: {e}", raw[:500].decode("utf-8", errors="replace"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace") if e.fp else str(e)
        die(f"HTTP {e.code}", error_body[:500])
    except URLError as e:
        if isinstance(e.reason, TimeoutError):
            die("Request timed out (60s)")
        die(f"Network error: {e.reason}")

    raw_path = f"/tmp/reddit_search_{os.getpid()}.json"
    with open(raw_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result, raw_path


def _fmt_int(val: Any) -> str:
    if val is None:
        return "0"
    return f"{int(val):,}"


def _fmt_date(epoch: Any) -> str:
    if not epoch:
        return "?"
    try:
        return datetime.fromtimestamp(float(epoch), tz=timezone.utc).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return "?"


def fmt_posts(result: Dict[str, Any]) -> str:
    data = result.get("data") or {}
    posts = data.get("posts") or []
    cursor = data.get("cursor")

    lines = [
        f"Results: {len(posts)}"
        f"{' | cursor=' + cursor if cursor else ''}",
        "",
    ]

    for i, thing in enumerate(posts, 1):
        d = thing.get("data") or {}
        title = (d.get("title") or "").replace("\n", " ").strip()
        flair = d.get("link_flair_text") or ""
        flair_str = f"[{flair}] " if flair else ""

        lines.append(f"{i}. {flair_str}{title}")
        lines.append(
            f"   r/{d.get('subreddit', '?')} · u/{d.get('author', '?')} · "
            f"{_fmt_date(d.get('created_utc'))} · "
            f"score={_fmt_int(d.get('score'))} comments={_fmt_int(d.get('num_comments'))}"
        )

        if d.get("is_self"):
            text = (d.get("selftext") or "").replace("\n", " ").strip()
            if text:
                lines.append(f"   {text}")
        elif d.get("url") and d.get("url") != f"https://www.reddit.com{d.get('permalink', '')}":
            lines.append(f"   → {d['url']}")

        lines.append("")

    if not posts:
        lines.append("(no posts)")

    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) < 2:
        print((__doc__ or "").strip(), file=sys.stderr)
        sys.exit(1)

    try:
        body = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        die(f"Invalid JSON body: {e}")

    result, raw_path = api_call(body)
    print(fmt_posts(result))
    print(f"\n[Raw JSON saved to {raw_path}]")


if __name__ == "__main__":
    main()
