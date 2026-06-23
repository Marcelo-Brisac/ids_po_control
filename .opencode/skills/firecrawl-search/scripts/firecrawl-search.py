#!/usr/bin/env python3
"""
Firecrawl Search — web / news / images search via Firecrawl v2.

Usage:
    python3 firecrawl-search.py '<json_body>'

Prints a per-source result list (web / news / images) with title,
url, snippet/date/position. Full raw response saved to
/tmp/firecrawl_search_<pid>.json.

JSON body = Firecrawl v2 /v2/search request body. See SKILL.md.
"""

import json
import os
import socket
import sys
from typing import Any, Dict, List, NoReturn, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE_URL = os.environ.get("FIRECRAWL_BASE_URL", "")
API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")

SNIPPET_CHARS = 200


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

    url = f"{BASE_URL}/v1/search"
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

    raw_path = f"/tmp/firecrawl_search_{os.getpid()}.json"
    with open(raw_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result, raw_path


def _clip(s: Any, n: int = SNIPPET_CHARS) -> str:
    if not isinstance(s, str):
        return ""
    s = s.replace("\n", " ").strip()
    return s if len(s) <= n else s[:n] + "…"


def fmt_web(items: List[Dict[str, Any]]) -> List[str]:
    lines = [f"=== web ({len(items)}) ==="]
    for it in items:
        pos = it.get("position", "?")
        title = _clip(it.get("title"), 160)
        url = it.get("url", "?")
        desc = _clip(it.get("description"))
        cat = it.get("category")
        cat_str = f" [{cat}]" if cat else ""
        lines.append(f"{pos}. {title}{cat_str}")
        lines.append(f"   {url}")
        if desc:
            lines.append(f"   {desc}")
    return lines


def fmt_news(items: List[Dict[str, Any]]) -> List[str]:
    lines = [f"=== news ({len(items)}) ==="]
    for it in items:
        pos = it.get("position", "?")
        title = _clip(it.get("title"), 160)
        url = it.get("url", "?")
        date = it.get("date") or "?"
        snippet = _clip(it.get("snippet") or it.get("description"))
        lines.append(f"{pos}. {title}")
        lines.append(f"   {url}  ·  {date}")
        if snippet:
            lines.append(f"   {snippet}")
    return lines


def fmt_images(items: List[Dict[str, Any]]) -> List[str]:
    lines = [f"=== images ({len(items)}) ==="]
    for it in items:
        pos = it.get("position", "?")
        title = _clip(it.get("title"), 120)
        img = it.get("imageUrl") or "?"
        page = it.get("url") or "?"
        dims = ""
        w, h = it.get("imageWidth"), it.get("imageHeight")
        if w and h:
            dims = f"  {w}×{h}"
        lines.append(f"{pos}. {title}{dims}")
        lines.append(f"   img:  {img}")
        lines.append(f"   page: {page}")
    return lines


def fmt_result(result: Dict[str, Any]) -> str:
    credits = result.get("creditsUsed", "?")
    sid = result.get("id", "?")
    warning = result.get("warning")

    header = f"credits={credits} · id={sid}"
    if warning:
        header += f"\n⚠ warning: {warning}"

    sections = []
    web = result.get("web") or []
    news = result.get("news") or []
    images = result.get("images") or []

    if isinstance(web, list) and web:
        sections.append("\n".join(fmt_web(web)))
    if isinstance(news, list) and news:
        sections.append("\n".join(fmt_news(news)))
    if isinstance(images, list) and images:
        sections.append("\n".join(fmt_images(images)))

    if not sections:
        sections.append("(no results)")

    return header + "\n\n" + "\n\n".join(sections)


def main() -> None:
    if len(sys.argv) < 2:
        print((__doc__ or "").strip(), file=sys.stderr)
        sys.exit(1)

    try:
        body = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        die(f"Invalid JSON body: {e}")

    if not isinstance(body, dict) or "query" not in body:
        die("Body must be a JSON object with a 'query' field")

    result, raw_path = api_call(body)
    print(fmt_result(result))
    print(f"\n[Raw JSON saved to {raw_path}]")


if __name__ == "__main__":
    main()
