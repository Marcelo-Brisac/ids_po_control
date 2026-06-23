# TikTok E-commerce API Reference

Pagesize max: `10` for all endpoints. Exceeding returns `"param error"`.
Regions: `US, GB, MX, ES, DE, IT, FR, ID, VN, MY, TH, PH, BR, JP, SG`

---

## 1. Product Categories — `product-category`

No parameters. Returns 3-level tree.

Each node: `c_code` (ID string), `c_name`, `sub[]`. Use `c_code` as `l1/l2/l3_category_id` in search.

27 L1 categories including: Home Supplies (10), Kitchenware (11), Womenswear (2), Menswear (3), Beauty & Personal Care (14), Shoes (6), Sports & Outdoor (9), Phones & Electronics (16), Food & Beverages (24), etc.

---

## 2. Product Search — `product-search`

### Filter fields

| Field | Type | Description |
|-------|------|-------------|
| `region` | string | Country code |
| `l1_category_id` | int | L1 category |
| `l2_category_id` | int | L2 category |
| `l3_category_id` | int | L3 category |
| `commission_rate_range` | `{min, max}` | Commission % range |
| `creator_count_range` | `{min, max}` | Creator count range |
| `units_sold_range` | `{min, max}` | Sales volume range |
| `shop_type` | int | 1=Local, 2=Cross-border |
| `is_free_shipping` | bool | Free shipping |
| `is_local_warehouse` | bool | Local warehouse |
| `is_top_selling` | bool | Top selling |
| `is_new_listed` | bool | Newly listed |
| `is_sshop` | bool | Fully managed shop product |

### Orderby (array)

`day7_units_sold`, `day7_gmv`, `commission_rate`, `total_units_sold`, `total_gmv`, `creator_count`

### Response `data.list[]`

| Field | Description |
|-------|-------------|
| `product_id` | Product ID (use for drill-down) |
| `title` | Product title |
| `price` | e.g. "$23.89 - 53.95" |
| `region` | Country |
| `cover` | Image URL |
| `category` | `{l1: {id, name}, l2: {id, name}, l3: {id, name}}` |
| `commission_rate` | e.g. "8%" |
| `product_rating` | float |
| `total_units_sold` | All-time sales |
| `total_gmv` | All-time revenue |
| `yday_units_sold` | Yesterday sales |
| `day7_units_sold` | 7-day sales |
| `day7_gmv` | 7-day revenue |
| `day28_units_sold` | 28-day sales |
| `day90_units_sold` | 90-day sales |
| `creator_count` | Affiliate creator count |
| `is_cross_border` | 0 or 1 |
| `is_fully_managed` | 0 or 1 |
| `is_free_shipping` | 0 or 1 |
| `shop.seller_id` | Shop ID |
| `shop.name` | Shop name |
| `shop.total_units_sold` | Shop total sales |
| `tiktok_url` | TikTok product page |
| `ctime` | Product creation time |

---

## 3. Top Selling — `product-top-selling`

### Filter fields

| Field | Type | Description |
|-------|------|-------------|
| `region` | string | Country |
| `category_id` | int | Category filter |
| `date_info` | object | `{"type": "day|week|month", "value": "..."}` |

Date formats: day=`"2026-04-01"`, week=`"2026-14"`, month=`"2026-04"`

### Orderby (array)

`units_sold`, `gmv`, `total_units_sold`, `total_gmv`, `growth_rate`

### Response `data.list[]`

Same as product search, plus `growth_rate`, `real_price`, `units_sold`, `gmv`.

---

## 4. Product Videos — `product-video-list`

### Filter fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `product_id` | string | Yes | Product ID |

### Orderby (object, not array)

`play_count`, `digg_count`, `comment_count`, `share_count`, `units_sold`, `gmv`

### Response `data.list[]`

| Field | Description |
|-------|-------------|
| `video_id` | Video ID |
| `uid` | Creator UID |
| `play_count` | Views |
| `digg_count` | Likes |
| `comment_count` | Comments |
| `share_count` | Shares |
| `sold_count` | Sales from video |
| `sale_amount` | Revenue from video |
| `create_date` | Date posted |
| `is_ad` | Ad flag |
| `region` | Country |
| `video.video_desc` | Description |
| `video.cover` | Thumbnail URL |
| `video.duration` | Seconds |
| `video.tiktok_url` | TikTok link |

---

## 5. Product Creators — `product-creator-list`

### Filter fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `product_id` | string | Yes | Product ID |

### Orderby (object, not array)

`units_sold`, `gmv`, `follower_count`, `digg_count`

### Response `data.list[]`

| Field | Description |
|-------|-------------|
| `uid` | Creator UID |
| `unique_id` | Handle (@xxx) |
| `nickname` | Display name |
| `avatar` | Avatar URL |
| `units_sold` | Sales by creator |
| `gmv` | Revenue by creator |
| `follower_count` | Followers |
| `aweme_count` | Video count |
| `category_id` | Creator category ID |
| `category_name` | Creator category |
| `region` | Creator region |
