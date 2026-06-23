---
name: tiktok-ecommerce-flash
description: "TikTok e-commerce research. Use when the user asks about TikTok Shop products, trending products, top-selling items, product rankings, affiliate creators promoting a product, or TikTok e-commerce videos. Covers product search, category browsing, top-selling rankings, product-related videos, and product affiliate creators."
---

# TikTok E-commerce Research

Research TikTok e-commerce products, rankings, videos, and creators.

## Error Handling

### REQUIRED: on HTTP 402 or "Subscription required"

When any script call returns `"error": "HTTP 402"` or `"Subscription required"`, you MUST execute these steps **in this exact order**:

1. **FIRST** — call the `suggest_subscription` tool with `feature: "tiktok-ecommerce"`. This is mandatory. Do not skip it. Do not merge it into the final answer. Do not reason about whether it's needed — always call it on 402.
2. **THEN** — stop using this skill entirely for the remainder of the turn.
3. **THEN** — answer the user's question using web search or other tools, and give a substantive fallback answer.

Do not proceed to step 2 before completing step 1. Do not proceed to step 3 before completing steps 1 and 2. If you skip step 1, the user's frontend will not show the upgrade prompt and the fix is incomplete.

The same rule applies if script calls fail due to missing env vars — call `suggest_subscription` with `feature: "tiktok-ecommerce"` first, then fall back.

### Other errors

If a call returns HTTP 429 (rate limit), retry after a short wait.

## Cost Discipline

Each call consumes credits. Make every call count:

- **Budget: 2–4 calls per user request** by default. If the user explicitly asks for broader exploration, you may exceed this.
- **Do NOT paginate** unless the user explicitly asks for more results.
- **Use precise filters** to get the right results in one call rather than broad searches followed by filtering.

## Usage

```bash
python3 scripts/tiktok-ecommerce.py <endpoint> '<json_body>'
```

Prints formatted summary to stdout. Raw JSON saved to a `/tmp/tiktok_ecommerce_*.json` file (path printed at end of output).

## Endpoints

### 1. Product Categories — get category IDs for search filters

```bash
python3 scripts/tiktok-ecommerce.py product-category '{}'
```

Output: L1 summary only (`[ID] Name (N L2, N L3)`). Full formatted tree saved to `/tmp/tiktok_ecommerce_categories.txt`. Grep that file for L2/L3 IDs, e.g. `grep -A20 '^\[14\] Beauty' /tmp/tiktok_ecommerce_categories.txt`.

### 2. Product Search — find products by keyword and filters

```bash
python3 scripts/tiktok-ecommerce.py product-search '{
  "keywords": "water bottle",
  "filter": {
    "region": "US",
    "l1_category_id": 11,
    "commission_rate_range": {"min": 10, "max": 20},
    "units_sold_range": {"min": 1000},
    "creator_count_range": {"min": 5},
    "shop_type": 2,
    "is_free_shipping": true,
    "is_top_selling": true,
    "is_new_listed": true,
    "is_local_warehouse": true,
    "is_sshop": true
  },
  "orderby": [{"field": "day7_units_sold", "order": "desc"}],
  "page": 1, "pagesize": 10
}'
```

**Pagesize max**: 10.

**Sort options**: `day7_units_sold`, `day7_gmv`, `commission_rate`, `total_units_sold`, `total_gmv`, `creator_count`

Output per product: ID, title, region, price, rating, commission, total/7d/28d sold, 7d GMV, creator count, category path, shop name, cross-border/fully-managed flags, TikTok URL.

### 3. Top Selling Rankings — top products by date period

```bash
python3 scripts/tiktok-ecommerce.py product-top-selling '{
  "filter": {
    "region": "US",
    "category_id": 14,
    "date_info": {"type": "day", "value": "2026-04-01"}
  },
  "orderby": [{"field": "units_sold", "order": "desc"}],
  "page": 1, "pagesize": 10
}'
```

**Date formats**: day=`"2026-04-01"`, week=`"2026-14"`, month=`"2026-04"`

**Sort options**: `units_sold`, `gmv`, `total_units_sold`, `total_gmv`, `growth_rate`

Output per product: ID, title, region, price, period sold/GMV, growth rate %, total sold/GMV, category, shop.

### 4. Product Videos — videos promoting a product

```bash
python3 scripts/tiktok-ecommerce.py product-video-list '{
  "filter": {"product_id": "1729421229342823356"},
  "orderby": {"field": "play_count", "order": "desc"},
  "page": 1, "pagesize": 10
}'
```

Note: `orderby` is an **object** (not array).

**Sort options**: `play_count`, `digg_count`, `comment_count`, `share_count`, `units_sold`, `gmv`

Output per video: description, video ID, creator UID, views/likes/comments/shares, sales/revenue, date, duration, ad flag, TikTok URL.

### 5. Product Creators — affiliate creators for a product

```bash
python3 scripts/tiktok-ecommerce.py product-creator-list '{
  "filter": {"product_id": "1729421229342823356"},
  "orderby": {"field": "units_sold", "order": "desc"},
  "page": 1, "pagesize": 10
}'
```

Note: `orderby` is an **object** (not array).

**Sort options**: `units_sold`, `gmv`, `follower_count`, `digg_count`

Output per creator: @handle, nickname, UID, region, followers, video count, sales, GMV, category.

## Workflow

1. **Start broad**: `product-search` or `product-top-selling` to find products
2. **Drill down**: use `product_id` from results with `product-video-list` and `product-creator-list`
3. **Filter by category**: run `product-category` first to get IDs, then search with `l1_category_id`

## Regions

`US, GB, MX, ES, DE, IT, FR, ID, VN, MY, TH, PH, BR, JP, SG`

## Full API Reference

For complete request/response field details, read [references/api.md](references/api.md).
