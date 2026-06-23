---
name: firecrawl-search
description: Web search via Firecrawl — returns real search results (web / news / images) with title, URL, snippet, position. Use whenever the user asks to search the web, find articles, research a topic, look up news or sources, find pages by topic — phrases like "search for", "find me", "look up", "what's happening with", "find articles about". Supports time/country/category filters, optional in-line scraping of each result's full page.
---

# Firecrawl Search

```bash
python3 scripts/firecrawl-search.py '<json_body>'
```

JSON body is the upstream `POST /v1/search` request body (Firecrawl
v2 schema). Prints per-source result list (web / news / images) with
title, url, snippet/date/position; full raw response is saved to
`/tmp/firecrawl_search_<pid>.json`.

## Request body

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `query` | string | ✅ | — | Search query. |
| `limit` | int | — | `5` | Per-source result cap. |
| `sources` | array | — | `["web"]` | Any of `web`, `images`, `news`. Mixed sources allowed: `["web","news"]`. Typed object form `[{"type":"web","tbs":"qdr:d","location":"US"}]` also accepted — per-source tbs / location overrides go in the object form only. |
| `tbs` | string | — | — | Time filter: `qdr:h` \| `qdr:d` \| `qdr:w` \| `qdr:m` \| `qdr:y`. Applies to all sources when set at top level. |
| `country` | string | — | — | ISO-3166-1 alpha-2 (e.g. `US`, `CN`, `JP`). |
| `location` | string | — | — | City/region string (e.g. `"New York"`). |
| `categories` | array | — | — | Filter by category: `github`, `research paper`, `news`, `pdf`, `tweet`, etc. String shorthand or `[{"type":"github"}]` object form both accepted. |
| `scrapeOptions` | object | — | — | When set, each result is also scraped with these options — see `firecrawl-scrape`'s body schema. **Charges scrape add-ons per result.** |
| `enterprise` | array | — | — | `["anon"]` and/or `["zdr"]` for enterprise auth tiers. `["zdr"]` costs **10 fc-credit / 10 results** instead of 2 (Zero Data Retention). |

The model has `extra='allow'`, so any v2 field not listed here is
passed through untouched.

## Response shape

Top level (envelope flattened by mule-router):

```jsonc
{
  "web": [
    { "url": "...", "title": "...", "description": "...", "position": 1, "category": "github"? }
  ],
  "news": [
    { "title": "...", "url": "...", "date": "1 day ago", "imageUrl": "...", "snippet"?: "...", "position": 1 }
  ],
  "images": [
    { "title": "...", "url": "...", "imageUrl": "...", "imageWidth": 932, "imageHeight": 584, "position": 1 }
  ],
  "creditsUsed": 2,
  "id":          "019e9268-...",   // search id, useful for upstream debugging
  "warning":     "..."             // optional
}
```

Only the source arrays you requested are present. Empty arrays
mean "zero hits", not an error.

## Pricing

- **Per 10 results: 2 fc-credit × 0.9 = 1.8 mulerun-credit** (standard).
- **Per 10 results: 10 fc-credit × 0.9 = 9 mulerun-credit** when
  `enterprise: ["zdr"]` (Zero Data Retention).
- Zero results — **not charged** (`creditsUsed=0`).
- `scrapeOptions` set — **each result also incurs scrape charges**
  (base 1 + json/stealth/pdf/zdr add-ons per result). Costs add up
  fast; prefer calling `firecrawl-scrape` selectively after seeing
  search results.

## Errors

The skill exits non-zero and prints a JSON `{error, detail}` blob to
stderr on:
- Missing env (`FIRECRAWL_BASE_URL` / `FIRECRAWL_API_KEY`)
- HTTP error (4xx/5xx)
- Network/timeout (180s)
- Invalid JSON in argument or response

| HTTP | Cause | Action |
|------|-------|--------|
| 4xx (422) | Bad payload (missing `query`, unsupported `sources` value) | Fix and retry. |
| 402 | `subscription_required` / out-of-credit | **Stop**, fall back to `WebSearch` or `multi-search`. |
| 5xx | Upstream Firecrawl transient | Retry **once** after short wait. |

## Examples

Basic web search (top 5):

```bash
python3 scripts/firecrawl-search.py '{"query": "claude 4.6 release"}'
```

News from the past day:

```bash
python3 scripts/firecrawl-search.py '{
  "query":   "openai sam altman",
  "sources": ["news"],
  "tbs":     "qdr:d",
  "limit":   10
}'
```

Mixed web + news + images:

```bash
python3 scripts/firecrawl-search.py '{
  "query":   "anthropic mcp",
  "sources": ["web", "news", "images"],
  "limit":   5
}'
```

Academic / GitHub filter:

```bash
python3 scripts/firecrawl-search.py '{
  "query":      "agent harness e2b sandbox",
  "categories": ["github", "research paper"],
  "limit":      10
}'
```

Search **and** scrape each result's full content (expensive — adds
~1 fc-credit per result):

```bash
python3 scripts/firecrawl-search.py '{
  "query":          "rust async runtime comparison",
  "limit":          5,
  "scrapeOptions":  {"formats": ["markdown"], "onlyMainContent": true}
}'
```

Country / location targeting:

```bash
python3 scripts/firecrawl-search.py '{
  "query":    "ramen near me",
  "country":  "JP",
  "location": "Tokyo"
}'
```

## Tips

- **Use `firecrawl-search` to find URLs, then `firecrawl-scrape` on the
  promising one(s).** Don't set `scrapeOptions` on search unless you
  actually need every result's full body — it multiplies cost.
- `--scrape`-equivalent (`scrapeOptions`) is the only way to get full
  page text from search in one call, but post-filter and call
  `firecrawl-scrape` separately when you only need 1–2 of N results.
- `id` in the response is the upstream search id; pass it to support
  if a query mis-ranks.
- This skill replaces the firecrawl MCP path — it doesn't support the
  `search-feedback` refund flow (that endpoint isn't exposed by
  mule-router).
