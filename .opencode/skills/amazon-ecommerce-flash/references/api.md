# Amazon E-commerce API Reference

Rate limit: 40 requests/minute. Data limit: top 2,000 results per query.
Marketplaces: `US, JP, UK, DE, FR, IT, ES, CA, IN, MX, BR, AU, AE`

---

## 1. Product Research — `product-research`

Discover products by multi-dimensional filters. Returns product-level metrics.

### Request fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `marketplace` | string | **Yes** | Marketplace code |
| `month` | string | | Query month (`yyyyMM`), supports last 24 months |
| `keyword` | string | | Search keyword |
| `matchType` | int | | `1` phrase, `2` fuzzy (default), `3` exact |
| `excludeKeywords` | string | | Exclude keywords |
| `includeBrands` | string | | Include brands |
| `excludeBrands` | string | | Exclude brands |
| `includeSellers` | string | | Include sellers |
| `excludeSellers` | string | | Exclude sellers |
| `minPrice` / `maxPrice` | float | | Price range |
| `minProfit` / `maxProfit` | float | | Gross margin range (%) |
| `minFba` / `maxFba` | float | | FBA fee range |
| `minUnits` / `maxUnits` | int | | Monthly sales range |
| `minRevenue` / `maxRevenue` | float | | Monthly revenue range |
| `minUnitsCr` / `maxUnitsCr` | float | | Sales growth rate range (%) |
| `minRevenueCr` / `maxRevenueCr` | float | | Revenue growth rate range (%) |
| `minBsr` / `maxBsr` | int | | BSR rank range |
| `minBsrCv` / `maxBsrCv` | int | | BSR 7-day growth value range |
| `minBsrCr` / `maxBsrCr` | float | | BSR 7-day growth rate range (%) |
| `minRating` / `maxRating` | float | | Rating value range |
| `minRatings` / `maxRatings` | int | | Review count range |
| `minRatingsCv` / `maxRatingsCv` | int | | Monthly new reviews range |
| `weightUnit` | string | | `g` (default), `kg`, `ounces`, `pounds` |
| `minWeights` / `maxWeights` | float | | Weight range |
| `dimensionType` | string | | Size tier codes, comma-separated (see Size Tiers) |
| `minVariations` / `maxVariations` | int | | Variation count range |
| `minSellers` / `maxSellers` | int | | Seller count range |
| `minLqs` / `maxLqs` | float | | Listing quality score range |
| `availableMonth` | int | | Listing age: `1`=30d, `3`=3mo, `6`=6mo, `12`=1yr, `24`=2yr |
| `sellerNation` | string | | Seller country, comma-separated (see Seller Countries) |
| `fulfillment` | string | | `AMZ`, `FBA`, `FBM` (comma-separated) |
| `badgeBS` | string | | Has Best Seller? `Y` |
| `badgeAC` | string | | Has Amazon's Choice? `Y` |
| `badgeNR` | string | | Has New Release? `Y` |
| `variation` | string | | `Y` = exclude variations (default if unspecified), `N` = include |
| `nodeIdPaths` | string[] | | Category node paths |
| `nodeIdPathEqual` | bool | | `true` = exact category, `false` = include subcategories |
| `filterSub` | string | | Filter sub-categories? `Y` |
| `minSubBsrRank` / `maxSubBsrRank` | int | | Sub-category rank range (only when `filterSub=Y`) |
| `page` | int | | Page number (default: 1) |
| `size` | int | | Results per page (default: 50, **max: 100**) |
| `order.field` | string | | Sort field (default: `total_units`). See Product Sort Fields |
| `order.desc` | bool | | `true` = descending (default) |

### Response `data.items[]`

| Field | Type | Description |
|-------|------|-------------|
| `asin` | string | Product ASIN |
| `title` | string | Product title |
| `brand` | string | Brand name |
| `brandUrl` | string | Brand URL |
| `imageUrl` | string | Product image URL |
| `parent` | string | Parent ASIN |
| `nodeIdPath` | string | Category node path |
| `nodeLabelPath` | string | Category label path (e.g. `Pet Supplies:Dogs:Health Supplies`) |
| `bsr` | int | BSR rank |
| `bsrCr` | float | BSR 7-day growth rate (%) |
| `bsrCv` | int | BSR 7-day growth value |
| `units` | int | Monthly sales (parent) |
| `unitsGr` | float | Sales growth rate (%) |
| `revenue` | float | Monthly revenue (parent) |
| `amzUnit` | int | Child ASIN last-30-day sales |
| `amzSales` | float | Child ASIN revenue |
| `price` | float | Current price |
| `profit` | float | Gross margin (%) |
| `fba` | float | FBA shipping fee |
| `ratings` | int | Total review count |
| `rating` | float | Average rating |
| `ratingsCv` | int | Monthly new reviews |
| `ratingDelta` | int | New reviews in last 30 days |
| `lqs` | float | Listing quality score |
| `availableDate` | long | Listing date (timestamp ms) |
| `fulfillment` | string | `AMZ`, `FBA`, or `FBM` |
| `variations` | int | Variation count |
| `sellers` | int | Seller count |
| `sellerName` | string | BuyBox seller name |
| `sellerId` | string | BuyBox seller ID |
| `sellerNation` | string | Seller country code |
| `weight` | string | Product weight |
| `dimension` | string | Product dimensions |
| `badge.bestSeller` | string | Best Seller badge (`Y`/`N`) |
| `badge.amazonChoice` | string | Amazon's Choice badge (`Y`/`N`) |
| `badge.newRelease` | string | New Release badge (`Y`/`N`) |
| `badge.ebc` | string | A+ content (`Y`/`N`) |
| `badge.video` | string | Has video (`Y`/`N`) |
| `subcategories` | list | Sub-category rankings: `code`, `rank`, `label` |

---

## 2. Competitor Lookup — `competitor-lookup`

Look up specific products by ASIN, brand, or seller. Returns same product-level metrics as product-research.

### Request fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `marketplace` | string | **Yes** | Marketplace code |
| `month` | string | | Query month (`yyyyMM`) |
| `asins` | string[] | | ASINs to look up. **Max 40** — split into batches if more |
| `brand` | string | | Brand name |
| `sellerName` | string | | Seller name |
| `keyword` | string | | Keyword to match in titles |
| `matchType` | int | | `1` phrase, `2` fuzzy (default), `3` exact |
| `nodeIdPath` | string | | Category node path |
| `nodeIdPathEqual` | bool | | `true` = exact category, `false` = include subcategories |
| `variation` | string | | `Y` = exclude variations, `N` = include |
| `page` | int | | Page number (default: 1) |
| `size` | int | | Results per page (default: 50, **max: 100**) |
| `order.field` | string | | Sort field (default: `total_units`). See Product Sort Fields |
| `order.desc` | bool | | `true` = descending (default) |

### Response `data.items[]`

Same fields as product-research (see above).

---

## 3. Keyword Research — `keyword-research`

Analyze keyword markets: search volume, competition, conversion potential.

### Request fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `marketplace` | string | **Yes** | Marketplace code |
| `month` | string | | Query month (`yyyyMM`) |
| `keywords` | string | | Keyword to research |
| `excludeKeywords` | string | | Exclude keywords |
| `departments` | string[] | | Category codes (e.g. `["automotive","baby-products"]`) |
| `minSearches` / `maxSearches` | int | | Monthly search volume range |
| `minSearchesCr` / `maxSearchesCr` | float | | Search volume growth rate (%) |
| `minSearchMonthCv` / `maxSearchMonthCv` | int | | YoY search volume growth value |
| `minSearchMonthCr` / `maxSearchMonthCr` | float | | YoY search volume growth rate (%) |
| `minSearchNearlyCv` / `maxSearchNearlyCv` | int | | Last 3 months search growth value |
| `minSearchNearlyCr` / `maxSearchNearlyCr` | float | | Last 3 months search growth rate (%) |
| `minProducts` / `maxProducts` | int | | Product count range |
| `minPurchases` / `maxPurchases` | int | | Monthly purchase volume range |
| `minPurchaseRate` / `maxPurchaseRate` | float | | Purchase rate range (%) |
| `minSupplyDemandRatio` / `maxSupplyDemandRatio` | float | | Supply/demand ratio range |
| `minGoodsValue` / `maxGoodsValue` | float | | Goods flow value range |
| `minAraClickRate` / `maxAraClickRate` | float | | Click concentration (%) |
| `minBid` / `maxBid` | float | | PPC bid range ($) |
| `minAvgPrice` / `maxAvgPrice` | float | | Average price range |
| `minRating` / `maxRating` | float | | Average rating range |
| `minRatings` / `maxRatings` | int | | Average review count range |
| `marketPeriod` | string | | Market cycle (see Market Periods) |
| `withYearlyGrowth` | bool | | `true` = emerging/new markets only |
| `minWordCount` / `maxWordCount` | int | | Keyword word count range |
| `page` | int | | Page number (default: 1) |
| `size` | int | | Results per page (default: 15, **max: 15**) |
| `order.field` | string | | Sort field (see Keyword Sort Fields) |
| `order.desc` | bool | | `true` = descending (default) |

### Response `data.items[]`

| Field | Type | Description |
|-------|------|-------------|
| `keywords` | string | Keyword |
| `keywordCn` | string | Chinese translation |
| `searches` | int | Monthly search volume |
| `clicks` | int | Total clicks |
| `impressions` | long | Total impressions |
| `purchases` | int | Monthly purchases |
| `purchaseRate` | float | Purchase rate (%) |
| `growth` | float | Search growth rate (%) |
| `products` | int | Competing product count |
| `supplyDemandRatio` | float | Supply/demand ratio (higher = less competition) |
| `searchMonthlyCv` | int | YoY search volume change |
| `searchMonthlyCr` | float | YoY search volume change rate (%) |
| `searchNearlyCv` | int | Last 3 months search change |
| `searchNearlyCr` | float | Last 3 months search change rate (%) |
| `avgPrice` | float | Average product price |
| `avgRatings` | int | Average review count |
| `avgRating` | float | Average rating value |
| `bidMin` / `bidMax` / `bid` | float | PPC bid range and median ($) |
| `araClickRate` | float | Click concentration (top 3 ASINs' share, %) |
| `araShareRate` | float | Shared conversion rate |
| `goodsValue` | float | Goods flow value |
| `marketPeriod` | string | Market cycle code |
| `hasBrandWord` | bool | Is this a branded keyword? |
| `brands` | string[] | Top brands |
| `categories` | string[] | Top categories |
| `araAsinList` | list | Top-clicked ASINs: `asin`, `clickRate`, `conversionShareRate` |

---

## Reference Tables

### Marketplaces

`US` (USD), `JP` (JPY), `UK` (GBP), `DE` (EUR), `FR` (EUR), `IT` (EUR), `ES` (EUR), `CA` (CAD), `IN` (INR), `MX` (MXN), `BR` (BRL), `AU` (AUD), `AE` (AED)

### Product Sort Fields

`total_units` (default), `total_amount`, `bsr_rank`, `price`, `rating`, `reviews`, `profit`, `reviews_rate`, `available_date`, `questions`, `total_units_growth`, `total_amount_growth`, `reviews_increasement`, `bsr_rank_cv`, `bsr_rank_cr`, `amz_unit`

### Keyword Sort Fields

`searches` (default), `keywordsIsHide` (purchase volume), `searches_growth`, `yearly_growth_rate`, `growth_rate_trend_min` (3mo growth), `monopoly_click_rate`, `goods_value`

### Market Periods

`N` = non-seasonal, `S1-S3` = peak Jan-Mar, `S4-S6` = peak Apr-Jun, `S7-S9` = peak Jul-Sep, `S10-S12` = peak Oct-Dec, `I` = continuously growing, `D` = continuously declining

### Seller Countries

`CN`, `HK`, `US`, `JP`, `GB`, `DE`, `FR`, `IT`, `ES`, `CA`, `IN`, `TR`, `TW`, `MX`, `AU`, `AE`, `BR`

### Size Tiers (US)

`ST`/`SS` = Small Standard, `LS` = Large Standard, `SO` = Small Oversize, `MO` = Medium Oversize, `LO`/`LB` = Large Oversize, `SP` = Special Oversize, `ELO` = Extra Large 0-50lb, `EL5O` = 50-70lb, `EL7O` = 70-150lb, `EL15O` = 150+lb

### API Response Envelope

```json
{"code": "OK", "message": "Success", "data": {"pages": 100, "page": 1, "size": 50, "total": 5000, "items": [...]}}
```

Error codes: `ERROR_PARAM`, `ERROR_SECRET_KEY`, `ERROR_SECRET_KEY_OVERDUE`, `ERROR_VISIT_MAX`, `ERROR_SECRET_KEY_INVALID`, `ERROR_SERVER_INTERNAL`
