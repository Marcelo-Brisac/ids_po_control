#!/usr/bin/env python3
"""
Firecrawl Scrape — single-page extraction (markdown / html / links / screenshot / json).

Usage:
    python3 firecrawl-scrape.py '<json_body>'

Prints a one-line metadata summary plus inline content for the
single-format case (markdown only); for multi-format requests prints
the format breakdown. Full raw response saved to
/tmp/firecrawl_scrape_<pid>.json.

JSON body = Firecrawl v2 /v2/scrape request body. See SKILL.md.
"""

import json
import os
import socket
import sys
from typing import Any, Dict, NoReturn, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE_URL = os.environ.get("FIRECRAWL_BASE_URL", "")
API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")

PREVIEW_CHARS = 4000


def die(msg: str, detail: Optional[str] = None) -> NoReturn:
    err: Dict[str, str] = {"error": msg}
    if detail:
        err["detail"] = detail
    print(json.dumps(err, indent=2), file=sys.stderr)
    sys.exit(1)


def api_call(body: Dict[str, Any]) -> tuple:
    if not BASE_URL:
        die("No base URL — set FIRECRAWL_BASE_URL")
    if not API_KEY:
        die("No API key — set FIRECRAWL_API_KEY")

    url = f"{BASE_URL}/v1/scrape"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "identity",
        "Authorization": f"Bearer {API_KEY}",
    }
    req = Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")

    try:
        with urlopen(req, timeout=180) as resp:
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
        if isinstance(e.reason, (TimeoutError, socket.timeout)):
            die("Request timed out (180s)")
        die(f"Network error: {e.reason}")

    raw_path = f"/tmp/firecrawl_scrape_{os.getpid()}.json"
    with open(raw_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result, raw_path


def fmt_metadata(result: Dict[str, Any]) -> str:
    meta = result.get("metadata") or {}
    title = (meta.get("title") or "").replace("\n", " ").strip()
    status = meta.get("statusCode", "?")
    src = meta.get("sourceURL") or meta.get("url") or "?"
    credits = result.get("creditsUsed") or meta.get("creditsUsed") or "?"
    cache = meta.get("cacheState") or "?"
    proxy = meta.get("proxyUsed") or "?"

    parts = [f"HTTP {status} · credits={credits} · cache={cache} · proxy={proxy}"]
    if title:
        parts.append(f"title: {title}")
    parts.append(f"src:   {src}")
    warning = result.get("warning")
    if warning:
        parts.append(f"⚠ warning: {warning}")
    return "\n".join(parts)


def fmt_body(result: Dict[str, Any]) -> str:
    """Pick the content fields present and show preview of each."""
    lines = []
    # Common content fields, in order of usefulness
    for key in ("markdown", "html", "rawHtml", "summary"):
        val = result.get(key)
        if isinstance(val, str) and val:
            preview = val if len(val) <= PREVIEW_CHARS else val[:PREVIEW_CHARS] + f"\n… [+{len(val) - PREVIEW_CHARS} chars]"
            lines.append(f"--- {key} ({len(val)} chars) ---")
            lines.append(preview)

    links = result.get("links")
    if isinstance(links, list) and links:
        lines.append(f"--- links ({len(links)}) ---")
        for u in links[:50]:
            lines.append(f"  {u}")
        if len(links) > 50:
            lines.append(f"  … [+{len(links) - 50} more]")

    screenshot = result.get("screenshot")
    if isinstance(screenshot, str) and screenshot:
        lines.append(f"--- screenshot ---")
        lines.append(f"  {screenshot}")

    jsn = result.get("json")
    if jsn is not None:
        lines.append("--- json (extracted) ---")
        lines.append(json.dumps(jsn, indent=2, ensure_ascii=False)[:PREVIEW_CHARS])

    actions = result.get("actions")
    if actions:
        lines.append(f"--- actions ({len(actions) if isinstance(actions, list) else '?'}) ---")
        lines.append("  (see raw JSON for action results)")

    if not lines:
        lines.append("(no content fields in response — see raw JSON)")

    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) < 2:
        print((__doc__ or "").strip(), file=sys.stderr)
        sys.exit(1)

    try:
        body = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        die(f"Invalid JSON body: {e}")

    if not isinstance(body, dict) or "url" not in body:
        die("Body must be a JSON object with a 'url' field")

    result, raw_path = api_call(body)
    print(fmt_metadata(result))
    print()
    print(fmt_body(result))
    print(f"\n[Raw JSON saved to {raw_path}]")


if __name__ == "__main__":
    main()
