#!/usr/bin/env python3
"""
Amazon E-commerce Research — product discovery, competitor lookup, and keyword market analysis.

Usage:
    python3 amazon-ecommerce.py <endpoint> '<json_body>'

Prints formatted summary to stdout. Saves raw JSON to /tmp/amazon_ecommerce_<endpoint>_<pid>.json.

Endpoints:
    product-research      Discover products by multi-dimensional filters (price, sales, BSR, margin, etc.)
    competitor-lookup      Look up specific ASINs, brands, or sellers for detailed metrics
    keyword-research       Analyze keyword markets: search volume, competition, conversion potential

Examples:
    python3 amazon-ecommerce.py keyword-research '{"marketplace":"US","keywords":"dog cone","page":1,"size":15}'
    python3 amazon-ecommerce.py product-research '{"marketplace":"US","keyword":"dog cone","matchType":1,"variation":"Y","page":1,"size":20}'
    python3 amazon-ecommerce.py competitor-lookup '{"marketplace":"US","asins":["B0CGCS344P","B0725C3RJX"],"variation":"Y","page":1,"size":20}'
"""

import json
import os
import sys
from typing import Any, Dict, List, NoReturn, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE_URL = os.environ.get("AMAZON_ECOMMERCE_BASE_URL", "")
API_KEY = os.environ.get("AMAZON_ECOMMERCE_API_KEY", "")

ENDPOINTS = {
    "product-research",
    "competitor-lookup",
    "keyword-research",
}


def die(msg: str, detail: Optional[str] = None) -> NoReturn:
    err: Dict[str, str] = {"error": msg}
    if detail:
        err["detail"] = detail
    print(json.dumps(err, indent=2), file=sys.stderr)
    sys.exit(1)


def api_call(endpoint: str, body: Dict[str, Any]) -> tuple:
    if not BASE_URL:
        die("No base URL — set AMAZON_ECOMMERCE_BASE_URL")
    if not API_KEY:
        die("No API key — set AMAZON_ECOMMERCE_API_KEY")

    url = f"{BASE_URL}/v1/{endpoint}"
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
                die(f"Empty response from {endpoint} (HTTP {resp.status})")
            try:
                result = json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                die(f"Invalid JSON from {endpoint}: {e}", raw[:500].decode("utf-8", errors="replace"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace") if e.fp else str(e)
        die(f"HTTP {e.code}", error_body[:500])
    except URLError as e:
        if isinstance(e.reason, TimeoutError):
            die("Request timed out (60s)")
        die(f"Network error: {e.reason}")

    slug = endpoint.replace("-", "_")
    raw_path = f"/tmp/amazon_ecommerce_{slug}_{os.getpid()}.json"
    with open(raw_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    code = result.get("code", "UNKNOWN")
    if code != "OK":
        die(
            f"API error: {code} — {result.get('message', '')}",
            f"Raw response saved to {raw_path}",
        )

    return result, raw_path


# =============================================================================
# Formatters
# =============================================================================

def _fmt_price(val: Any) -> str:
    if val is None:
        return "N/A"
    return f"${float(val):,.2f}"


def _fmt_pct(val: Any) -> str:
    if val is None:
        return "N/A"
    return f"{float(val):.1f}%"


def _fmt_int(val: Any) -> str:
    if val is None:
        return "N/A"
    return f"{int(val):,}"


def _badges(p: Dict[str, Any]) -> str:
    badge = p.get("badge", {}) or {}
    tags: List[str] = []
    if badge.get("bestSeller") not in (None, "N", ""):
        tags.append("BestSeller")
    if badge.get("amazonChoice") not in (None, "N", ""):
        tags.append("AmazonChoice")
    if badge.get("newRelease") not in (None, "N", ""):
        tags.append("NewRelease")
    if badge.get("ebc") not in (None, "N", ""):
        tags.append("A+")
    if badge.get("video") not in (None, "N", ""):
        tags.append("Video")
    return ", ".join(tags) if tags else ""


def fmt_product(p: Dict[str, Any], idx: int) -> str:
    lines: List[str] = []
    title = (p.get("title") or "?")[:80]
    lines.append(f"{idx}. {p.get('asin', '?')} | {title}")
    lines.append(f"   Price: {_fmt_price(p.get('price'))} | BSR: {_fmt_int(p.get('bsr'))} | Rating: {p.get('rating', '?')} ({_fmt_int(p.get('ratings'))} reviews)")
    lines.append(f"   Sales: {_fmt_int(p.get('units'))}/mo | Revenue: {_fmt_price(p.get('revenue'))}/mo | Growth: {_fmt_pct(p.get('unitsGr'))}")
    lines.append(f"   Margin: {_fmt_pct(p.get('profit'))} | FBA fee: {_fmt_price(p.get('fba'))} | Sellers: {p.get('sellers', '?')} | Fulfillment: {p.get('fulfillment', '?')}")
    lines.append(f"   Brand: {p.get('brand', '?')} | Seller country: {p.get('sellerNation', '?')}")
    cat = p.get("nodeLabelPath", "")
    if cat:
        lines.append(f"   Category: {cat[:90]}")
    b = _badges(p)
    if b:
        lines.append(f"   Badges: {b}")
    lines.append("")
    return "\n".join(lines)


def fmt_product_list(data: Dict[str, Any]) -> str:
    total = data.get("total", 0)
    items = data.get("items", [])
    lines = [f"Total: {total} | Page: {data.get('page', '?')} | Showing: {len(items)}\n"]
    for i, p in enumerate(items, 1):
        lines.append(fmt_product(p, i))
    return "\n".join(lines)


def fmt_keyword_list(data: Dict[str, Any]) -> str:
    total = data.get("total", 0)
    items = data.get("items", [])
    lines = [f"Total: {total} | Page: {data.get('page', '?')} | Showing: {len(items)}\n"]
    for i, k in enumerate(items, 1):
        kw = k.get("keywords", "?")
        cn = k.get("keywordCn", "")
        cn_str = f" ({cn})" if cn else ""
        lines.append(f'{i}. "{kw}"{cn_str}')
        lines.append(f"   Searches: {_fmt_int(k.get('searches'))}/mo | Purchases: {_fmt_int(k.get('purchases'))}/mo | Purchase rate: {_fmt_pct(k.get('purchaseRate'))}")
        lines.append(f"   Products: {_fmt_int(k.get('products'))} | Supply/demand: {k.get('supplyDemandRatio', '?')} | Click concentration: {_fmt_pct(k.get('araClickRate'))}")
        lines.append(f"   Avg price: {_fmt_price(k.get('avgPrice'))} | PPC bid: {_fmt_price(k.get('bid'))} ({_fmt_price(k.get('bidMin'))}~{_fmt_price(k.get('bidMax'))})")
        lines.append(f"   Growth: {_fmt_pct(k.get('growth'))} | YoY: {_fmt_pct(k.get('searchMonthlyCr'))} | 3mo: {_fmt_pct(k.get('searchNearlyCr'))} | Cycle: {k.get('marketPeriod', '?')}")
        # Top ASINs if present
        ara = k.get("araAsinList") or []
        if ara:
            top3 = ", ".join(f"{a.get('asin','')}({_fmt_pct(a.get('clickRate'))})" for a in ara[:3])
            lines.append(f"   Top ASINs: {top3}")
        lines.append("")
    return "\n".join(lines)


FORMATTERS = {
    "product-research": fmt_product_list,
    "competitor-lookup": fmt_product_list,
    "keyword-research": fmt_keyword_list,
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
