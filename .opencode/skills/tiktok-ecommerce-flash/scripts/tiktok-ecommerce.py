#!/usr/bin/env python3
"""
TikTok E-commerce Research — product data, rankings, videos, and creators.

Usage:
    python3 tiktok-ecommerce.py <endpoint> '<json_body>'

Prints formatted summary to stdout. Saves raw JSON to /tmp/tiktok_ecommerce_<endpoint>_<pid>.json.

Endpoints:
    product-search      Search products by keyword and filters
    product-category    Get category tree (IDs for search filters)
    product-top-selling Top selling product rankings by date period
    product-video-list  Videos promoting a specific product
    product-creator-list Affiliate creators for a specific product

Examples:
    python3 tiktok-ecommerce.py product-category '{}'
    python3 tiktok-ecommerce.py product-search '{"keywords":"shoes","filter":{"region":"US"},"page":1,"pagesize":10}'
    python3 tiktok-ecommerce.py product-top-selling '{"filter":{"region":"US","date_info":{"type":"day","value":"2026-04-01"}}}'
    python3 tiktok-ecommerce.py product-video-list '{"filter":{"product_id":"1729421229342823356"},"page":1,"pagesize":10}'
    python3 tiktok-ecommerce.py product-creator-list '{"filter":{"product_id":"1729421229342823356"},"page":1,"pagesize":10}'
"""

import json
import os
import sys
from typing import Any, Dict, List, NoReturn, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE_URL = os.environ.get("TIKTOK_ECOMMERCE_BASE_URL", "")
API_KEY = os.environ.get("TIKTOK_ECOMMERCE_API_KEY", "")

ENDPOINTS = {
    "product-search",
    "product-category",
    "product-top-selling",
    "product-video-list",
    "product-creator-list",
}


def die(msg: str, detail: Optional[str] = None) -> NoReturn:
    err: Dict[str, str] = {"error": msg}
    if detail:
        err["detail"] = detail
    print(json.dumps(err, indent=2), file=sys.stderr)
    sys.exit(1)


def api_call(endpoint: str, body: Dict[str, Any]) -> tuple[Dict[str, Any], str]:
    if not BASE_URL:
        die("No base URL — set TIKTOK_ECOMMERCE_BASE_URL")
    if not API_KEY:
        die("No API key — set TIKTOK_ECOMMERCE_API_KEY")

    url = f"{BASE_URL}/v1/{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    req = Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")

    try:
        with urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
    except HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        die(f"HTTP {e.code}", error_body[:500])
    except URLError as e:
        if isinstance(e.reason, TimeoutError):
            die("Request timed out")
        die(f"Network error: {e.reason}")

    # Save raw response to unique file
    slug = endpoint.replace("-", "_")
    raw_path = f"/tmp/tiktok_ecommerce_{slug}_{os.getpid()}.json"
    with open(raw_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    if result.get("code") != 0:
        die(
            f"API error code {result.get('code')}: {result.get('msg') or result.get('message', '')}",
            f"Raw response saved to {raw_path}",
        )

    return result, raw_path


# =============================================================================
# Formatters
# =============================================================================

def _shop_name(p: Dict[str, Any]) -> str:
    shop = p.get("shop")
    if isinstance(shop, dict):
        return shop.get("name", "?")
    return "?"


def _cat_path(p: Dict[str, Any]) -> str:
    cat = p.get("category", {})
    parts = []
    for level in ["l1", "l2", "l3"]:
        node = cat.get(level)
        if isinstance(node, dict) and node.get("name"):
            parts.append(node["name"])
    return " > ".join(parts) if parts else "?"


def fmt_categories(data: Any) -> str:
    cats: List[Dict[str, Any]] = data if isinstance(data, list) else []

    # Save full formatted tree to file for grep
    full_lines = []
    for c in cats:
        full_lines.append(f"[{c['c_code']}] {c['c_name']}")
        for sub in c.get("sub", []):
            full_lines.append(f"  [{sub['c_code']}] {sub['c_name']}")
            for s3 in sub.get("sub", []):
                full_lines.append(f"    [{s3['c_code']}] {s3['c_name']}")
    tree_path = "/tmp/tiktok_ecommerce_categories.txt"
    with open(tree_path, "w") as f:
        f.write("\n".join(full_lines) + "\n")

    # Print L1 summary only
    summary = [f"{len(cats)} L1 categories (full tree saved to {tree_path}):\n"]
    for c in cats:
        sub_count = sum(len(s.get("sub", [])) for s in c.get("sub", []))
        summary.append(f"  [{c['c_code']}] {c['c_name']} ({len(c.get('sub', []))} L2, {sub_count} L3)")
    return "\n".join(summary)


def fmt_product_search(data: Dict[str, Any]) -> str:
    lines = [f"Total: {data.get('total', 0)} | Showing: {len(data.get('list', []))}\n"]
    for i, p in enumerate(data.get("list", []), 1):
        lines.append(f"{i}. {p.get('title', '?')}")
        lines.append(f"   ID: {p.get('product_id')} | Region: {p.get('region')}")
        lines.append(f"   Price: {p.get('price')} | Rating: {p.get('product_rating', '?')} | Commission: {p.get('commission_rate', '?')}")
        lines.append(f"   Total sold: {int(p.get('total_units_sold', 0)):,} | 7d sold: {int(p.get('day7_units_sold', 0)):,} | 7d GMV: ${float(p.get('day7_gmv', 0)):,.2f}")
        lines.append(f"   28d sold: {int(p.get('day28_units_sold', 0)):,} | Creators: {int(p.get('creator_count', 0)):,}")
        lines.append(f"   Category: {_cat_path(p)}")
        lines.append(f"   Shop: {_shop_name(p)} | Cross-border: {'Yes' if p.get('is_cross_border') else 'No'} | Fully managed: {'Yes' if p.get('is_fully_managed') else 'No'}")
        lines.append(f"   TikTok: {p.get('tiktok_url', '')}")
        lines.append("")
    return "\n".join(lines)


def fmt_top_selling(data: Dict[str, Any]) -> str:
    lines = [f"Total: {data.get('total', 0)} | Showing: {len(data.get('list', []))}\n"]
    for i, p in enumerate(data.get("list", []), 1):
        lines.append(f"{i}. {p.get('title', '?')}")
        lines.append(f"   ID: {p.get('product_id')} | Region: {p.get('region')}")
        lines.append(f"   Price: {p.get('real_price', p.get('price', '?'))}")
        lines.append(f"   Period sold: {int(p.get('units_sold', 0)):,} | Period GMV: ${float(p.get('gmv', 0)):,.2f} | Growth: {p.get('growth_rate', '?')}%")
        lines.append(f"   Total sold: {int(p.get('total_units_sold', 0)):,} | Total GMV: ${float(p.get('total_gmv', 0)):,.2f}")
        lines.append(f"   Category: {_cat_path(p)} | Shop: {_shop_name(p)}")
        lines.append("")
    return "\n".join(lines)


def fmt_videos(data: Dict[str, Any]) -> str:
    lines = [f"Total: {data.get('total', 0)} | Showing: {len(data.get('list', []))}\n"]
    for i, v in enumerate(data.get("list", []), 1):
        vid = v.get("video", {})
        desc = (vid.get("video_desc") or "").strip()[:100]
        lines.append(f"{i}. {desc or '(no description)'}")
        lines.append(f"   Video ID: {v.get('video_id')} | Creator UID: {v.get('uid')}")
        lines.append(f"   Views: {int(v.get('play_count', 0)):,} | Likes: {int(v.get('digg_count', 0)):,} | Comments: {int(v.get('comment_count', 0)):,} | Shares: {int(v.get('share_count', 0)):,}")
        lines.append(f"   Sales: {int(v.get('sold_count', 0)):,} | Revenue: ${float(v.get('sale_amount', 0)):,.2f}")
        lines.append(f"   Date: {v.get('create_date', vid.get('create_time', '?'))} | Duration: {vid.get('duration', '?')}s | Ad: {'Yes' if str(v.get('is_ad')) == '1' else 'No'}")
        lines.append(f"   TikTok: {vid.get('tiktok_url', '')}")
        lines.append("")
    return "\n".join(lines)


def fmt_creators(data: Dict[str, Any]) -> str:
    lines = [f"Total: {data.get('total', 0)} | Showing: {len(data.get('list', []))}\n"]
    for i, c in enumerate(data.get("list", []), 1):
        lines.append(f"{i}. @{c.get('unique_id', '?')} ({c.get('nickname', '?')})")
        lines.append(f"   UID: {c.get('uid')} | Region: {c.get('region', '?')}")
        lines.append(f"   Followers: {int(c.get('follower_count', 0)):,} | Videos: {int(c.get('aweme_count', 0)):,}")
        lines.append(f"   Sales: {int(c.get('units_sold', 0)):,} | GMV: ${float(c.get('gmv', 0)):,.2f}")
        lines.append(f"   Category: {c.get('category_name', '?')}")
        lines.append("")
    return "\n".join(lines)


FORMATTERS = {
    "product-category": fmt_categories,
    "product-search": fmt_product_search,
    "product-top-selling": fmt_top_selling,
    "product-video-list": fmt_videos,
    "product-creator-list": fmt_creators,
}


def main() -> None:
    if len(sys.argv) < 3:
        print((__doc__ or "").strip(), file=sys.stderr)
        sys.exit(1)

    endpoint = sys.argv[1]
    if endpoint not in ENDPOINTS:
        die(f"Unknown endpoint '{endpoint}'. Valid: {', '.join(sorted(ENDPOINTS))}")

    try:
        body = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        die(f"Invalid JSON body: {e}")

    result, raw_path = api_call(endpoint, body)
    data = result.get("data", {})

    formatter = FORMATTERS.get(endpoint)
    if formatter:
        print(formatter(data))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    print(f"\n[Raw JSON saved to {raw_path}]")


if __name__ == "__main__":
    main()
