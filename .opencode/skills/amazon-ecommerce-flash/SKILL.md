---
name: amazon-ecommerce-flash
description: "Amazon e-commerce market research. Use when the user asks about Amazon products, market analysis, competitor analysis, keyword research, product discovery, BSR rankings, sales data, or Amazon seller intelligence. Covers product discovery by filters, competitor ASIN/brand/seller lookup, and keyword market analysis (search volume, competition, PPC bids)."
---

# Amazon E-commerce Market Research

Research Amazon products, competitors, and keyword markets.

## Error Handling

### REQUIRED: on HTTP 402 or "Subscription required"

When any script call returns `"error": "HTTP 402"` or `"Subscription required"`, you MUST execute these steps **in this exact order**:

1. **FIRST** — call the `suggest_subscription` tool with `feature: "amazon-ecommerce"`. This is mandatory. Do not skip it. Do not merge it into the final answer. Do not reason about whether it's needed — always call it on 402.
2. **THEN** — stop using this skill entirely for the remainder of the turn.
3. **THEN** — answer the user's question using web search or other tools, and give a substantive fallback answer.

Do not proceed to step 2 before completing step 1. Do not proceed to step 3 before completing steps 1 and 2. If you skip step 1, the user's frontend will not show the upgrade prompt and the fix is incomplete.

The same rule applies if script calls fail due to missing env vars — call `suggest_subscription` with `feature: "amazon-ecommerce"` first, then fall back.

### Other errors

If a call returns HTTP 429 (rate limit), retry after a short wait.

## Cost Discipline

Each call consumes credits. Make every call count:

- **Budget: 3–5 calls per user request** by default. If the user explicitly asks for broader exploration, you may exceed this.
- **Do NOT search for variations of the same keyword.** One keyword-research call per core keyword is enough.
- **Do NOT paginate** unless the user explicitly asks for more data. Page 1 is sufficient for analysis.
- **Do NOT cross-validate with competitor-lookup** unless the user asks for specific ASIN deep-dives. product-research already returns the same fields.
- **Prefer fewer calls with broader filters** over many calls with narrow filters.

## Usage

```bash
python3 scripts/amazon-ecommerce.py <endpoint> '<json_body>'
```

Prints formatted summary to stdout. Raw JSON saved to `/tmp/amazon_ecommerce_*.json` (path printed at end of output).

## Endpoints

### 1. Keyword Research — analyze keyword market demand and competition

```bash
python3 scripts/amazon-ecommerce.py keyword-research '{
  "marketplace": "US",
  "keywords": "dog cone",
  "page": 1,
  "size": 15,
  "order": {"field": "searches", "desc": true}
}'
```

**Pagesize max**: 15.

**Sort options**: `searches`, `keywordsIsHide` (purchase volume), `searches_growth`, `yearly_growth_rate`, `growth_rate_trend_min` (3mo growth), `monopoly_click_rate`, `goods_value`

**Key filters**: `minSearches`/`maxSearches`, `minPurchaseRate`/`maxPurchaseRate`, `minSupplyDemandRatio`/`maxSupplyDemandRatio`, `minBid`/`maxBid`, `minAraClickRate`/`maxAraClickRate`, `marketPeriod`, `withYearlyGrowth` (emerging markets only), `departments` (category codes array)

Output per keyword: keyword (with Chinese translation), monthly searches, purchases, purchase rate, product count, supply/demand ratio, click concentration, avg price, PPC bid range, growth rates (monthly/YoY/3mo), market cycle, top ASINs.

**Interpreting results (seller decision signals):**
- High searches + high supply/demand ratio = strong demand, manageable competition
- Positive growth rate = market is growing
- High purchase rate = keyword drives real conversions
- Low PPC bid + reasonable avg price = good ROI potential
- Low click concentration = no monopoly, easier to enter

### 2. Product Research — discover products by multi-dimensional filters

```bash
python3 scripts/amazon-ecommerce.py product-research '{
  "marketplace": "US",
  "keyword": "folding grill table",
  "matchType": 1,
  "variation": "Y",
  "minUnits": 100,
  "maxRatings": 500,
  "minPrice": 15,
  "maxPrice": 200,
  "page": 1,
  "size": 20,
  "order": {"field": "total_units_growth", "desc": true}
}'
```

**Pagesize max**: 100.

**Sort options**: `total_units` (default), `total_amount`, `bsr_rank`, `price`, `rating`, `reviews`, `profit`, `reviews_rate`, `available_date`, `total_units_growth`, `total_amount_growth`, `reviews_increasement`, `bsr_rank_cv`, `bsr_rank_cr`

**Key filters**: `keyword` + `matchType`, price/profit/FBA ranges, sales/revenue ranges and growth rates, BSR range and growth, rating/review ranges, weight/dimensions, `sellerNation`, `fulfillment` (AMZ/FBA/FBM), badges (`badgeBS`/`badgeAC`/`badgeNR`), `availableMonth` (listing age), `nodeIdPaths` (categories), `variation` (Y=exclude, N=include)

Output per product: ASIN, title, price, BSR, rating/reviews, monthly sales/revenue, growth rate, margin, FBA fee, seller count, brand, seller country, category path, badges.

### 3. Competitor Lookup — look up specific ASINs, brands, or sellers

```bash
python3 scripts/amazon-ecommerce.py competitor-lookup '{
  "marketplace": "US",
  "asins": ["B0CGCS344P", "B0725C3RJX", "B0CR9W611Q"],
  "variation": "Y",
  "page": 1,
  "size": 20,
  "order": {"field": "total_units", "desc": true}
}'
```

**Max 40 ASINs per request** — split into multiple calls if more.

**Pagesize max**: 100.

**Lookup by**: `asins` (array), `brand` (string), `sellerName` (string), `keyword` (title match)

Output: same product fields as product-research.

## Workflow

Plan your calls before executing. Pick the minimum set needed:

1. **Market validation**: 1 call — `keyword-research` with the product keyword
2. **Product discovery**: 1 call — `product-research` with keyword + filters (size 20–50 is enough)
3. **Competitor deep-dive**: 1 call — `competitor-lookup` with top ASINs from step 2 (only if user needs ASIN-level detail)

### Common Patterns (with call counts)

**Product + market analysis** (2–3 calls):
1. `keyword-research` — assess demand (1 call)
2. `product-research` — scan competitive landscape (1 call)
3. `competitor-lookup` — only if user provides specific ASINs (1 call, optional)

**Category discovery** (1–2 calls):
1. `product-research` with growth/review filters — find opportunities (1 call)
2. `keyword-research` with `withYearlyGrowth: true` — only if user wants trending keywords (1 call, optional)

**Full market report** (3 calls max):
1. `keyword-research` — demand landscape (1 call, page 1 only)
2. `product-research` — supply landscape (1 call, size 50)
3. `competitor-lookup` — top ASINs from step 2 (1 call)

## Marketplaces

`US`, `JP`, `UK`, `DE`, `FR`, `IT`, `ES`, `CA`, `IN`, `MX`, `BR`, `AU`, `AE`

## Full API Reference

For complete request/response field details, read [references/api.md](references/api.md).
