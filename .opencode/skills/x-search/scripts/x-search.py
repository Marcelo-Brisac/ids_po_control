#!/usr/bin/env python3
"""
X (Twitter) Search Recent — search public posts from the last 7 days.

Usage:
    python3 x-search.py '<json_body>'

Prints formatted summary to stdout. Saves raw JSON to /tmp/x_search_<pid>.json.

Body fields (see SKILL.md for full schema):
    query (required), max_results (10..100, default 10), start_time, end_time,
    since_id, until_id, sort_order (relevancy|recency), next_token.

The script always requests author_id + user expansion + standard tweet/user
fields so the summary can include @handle and engagement metrics. Callers do
not need to set tweet_fields/expansions/user_fields.

It also auto-injects noise filters into `query` unless the caller already
uses the relevant operator:
  -is:reply, min_likes:1, min_replies:1
  lang:en (only when the query is ASCII; suppressed if any `lang:` is set)
`sort_order` is left unset so the API uses its `relevancy` default — pass
`"sort_order":"recency"` only when timeline order matters.

Note: `min_faves:` and `min_retweets:` are Standard/Premium operators —
the v2 endpoint rejects them with HTTP 500. Use `min_likes:` instead.
Phrase wildcards (`"foo * bar"`) are silently ignored — treated as
`"foo bar"`. Don't rely on them.

Example:
    python3 x-search.py '{"query":"\"Claude 4.6\" -is:retweet","max_results":20,"sort_order":"recency"}'
"""

import json
import os
import sys
from typing import Any, Dict, NoReturn, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE_URL = os.environ.get("X_SEARCH_BASE_URL", "")
API_KEY = os.environ.get("X_SEARCH_API_KEY", "")


def die(msg: str, detail: Optional[str] = None) -> NoReturn:
    err: Dict[str, str] = {"error": msg}
    if detail:
        err["detail"] = detail
    print(json.dumps(err, indent=2), file=sys.stderr)
    sys.exit(1)


def augment_query(q: str) -> tuple:
    """Inject default noise filters into the query. Each filter is suppressed
    if the caller already mentions the relevant operator anywhere in the query
    (so `is:retweet` or `-is:retweet` both block the auto-add of `-is:retweet`)."""
    ql = q.lower()
    added = []

    def add(op_marker: str, to_append: str) -> None:
        if op_marker not in ql:
            added.append(to_append)

    add("is:reply",     "-is:reply")
    add("min_likes:",   "min_likes:1")
    add("min_replies:", "min_replies:1")
    # ASCII-only query → assume English. Any `lang:` operator opts out.
    if "lang:" not in ql and q.isascii():
        added.append("lang:en")

    if added:
        q = f"{q} {' '.join(added)}"
    return q, added


def api_call(body: Dict[str, Any]) -> tuple:
    if not BASE_URL:
        die("No base URL — set X_SEARCH_BASE_URL")
    if not API_KEY:
        die("No API key — set X_SEARCH_API_KEY")

    original_query = body.get("query", "")
    body["query"], added_filters = augment_query(original_query)

    # Force the field set we summarize on. Caller-provided values are kept.
    body.setdefault("tweet_fields", ["created_at", "public_metrics", "lang"])
    body.setdefault("expansions", ["author_id"])
    body.setdefault("user_fields", ["username", "name", "verified"])

    url = f"{BASE_URL}/v1/search-recent"
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

    raw_path = f"/tmp/x_search_{os.getpid()}.json"
    with open(raw_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result, raw_path, added_filters


def _fmt_int(val: Any) -> str:
    if val is None:
        return "0"
    return f"{int(val):,}"


def _users_by_id(result: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    users = (result.get("includes") or {}).get("users") or []
    return {u["id"]: u for u in users if u.get("id")}


def fmt_posts(result: Dict[str, Any]) -> str:
    posts = result.get("data") or []
    meta = result.get("meta") or {}
    users = _users_by_id(result)

    lines = [
        f"Results: {meta.get('result_count', len(posts))}"
        f"{' | next_token=' + meta['next_token'] if meta.get('next_token') else ''}",
        "",
    ]

    for i, p in enumerate(posts, 1):
        user = users.get(p.get("author_id", ""), {})
        handle = f"@{user['username']}" if user.get("username") else "?"
        name = user.get("name", "")
        if name and name != user.get("username"):
            handle = f"{handle} ({name})"

        m = p.get("public_metrics") or {}
        engagement = (
            f"likes={_fmt_int(m.get('like_count'))} "
            f"rt={_fmt_int(m.get('retweet_count'))} "
            f"reply={_fmt_int(m.get('reply_count'))} "
            f"views={_fmt_int(m.get('impression_count'))}"
        )

        created = (p.get("created_at") or "")[:19]
        lang = p.get("lang") or ""

        lines.append(f"{i}. {handle} · {created}{(' · ' + lang) if lang else ''}")
        lines.append(f"   {engagement}")
        text = (p.get("text") or "").replace("\n", " ").strip()
        lines.append(f"   {text}")
        lines.append(f"   https://x.com/i/status/{p.get('id', '')}")
        lines.append("")

    if not posts:
        errors = result.get("errors") or []
        if errors:
            lines.append(f"(no posts; {len(errors)} partial errors)")
        else:
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

    result, raw_path, added_filters = api_call(body)
    if added_filters:
        print(f"[auto-filters added: {' '.join(added_filters)}]")
    print(fmt_posts(result))
    print(f"\n[Raw JSON saved to {raw_path}]")


if __name__ == "__main__":
    main()
