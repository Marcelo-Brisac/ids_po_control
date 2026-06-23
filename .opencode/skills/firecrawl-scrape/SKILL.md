---
name: firecrawl-scrape
description: Scrape a single web page and return clean markdown (or HTML, links, screenshot, structured JSON). Use whenever the user provides a URL and wants its content — "scrape", "fetch", "grab", "read this page", "extract from this URL". Handles JS-rendered SPAs, supports custom actions/wait, redact-PII, multi-format extraction. Prefer this over WebFetch for any webpage content extraction.
---

# Firecrawl Scrape

```bash
python3 scripts/firecrawl-scrape.py '<json_body>'
```

JSON body is the upstream `POST /v1/scrape` request body (Firecrawl v2
schema). Prints a one-line metadata summary plus the inline content
(markdown for `formats=["markdown"]`, otherwise the format breakdown);
full raw response is saved to `/tmp/firecrawl_scrape_<pid>.json`.

## Request body

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `url` | string | ✅ | — | Absolute URL to scrape. |
| `formats` | array | — | `["markdown"]` | Any of `markdown`, `html`, `rawHtml`, `links`, `screenshot`, `summary`, plus typed `{type:"json", ...}`, `{type:"screenshot", fullPage, viewport}`, `{type:"changeTracking"}`, `{type:"question", prompt}`. Multiple formats return a JSON object keyed by format name. |
| `onlyMainContent` | bool | — | `false` | Strip nav/footer/sidebar. |
| `waitFor` | int (ms) | — | — | Wait for JS render before scraping. |
| `timeout` | int (ms) | — | `60000` | Hard cap per page. |
| `includeTags` / `excludeTags` | array | — | — | HTML tag whitelist/blacklist. |
| `headers` | object | — | — | Custom HTTP headers for the upstream fetch. |
| `actions` | array | — | — | Click / type / wait / screenshot steps before extraction (see Firecrawl v2 docs). |
| `parsers` | array | — | — | E.g. `[{"type":"pdf","mode":"auto","maxPages":50}]` — needed for PDFs. |
| `location` | object | — | — | `{country, languages[]}` geo-targeting. |
| `proxy` | enum | — | `basic` | `basic` \| `stealth` (+4 credits). |
| `removeBase64Images` | bool | — | `false` | Strip embedded `data:image` payloads. |
| `blockAds` | bool | — | `true` | |
| `storeInCache` | bool | — | `true` | Disable to force fresh fetch. |
| `zeroDataRetention` | bool | — | `false` | Enterprise — disables upstream logging (+1 credit). |
| `redactPii` (extra) | bool | — | `false` | Server-side PII redaction. |

The model has `extra='allow'`, so any v2 field not listed here is
passed through to upstream untouched.

## Response shape

Top level (envelope flattened by mule-router):

```jsonc
{
  "markdown":   "...",                    // when "markdown" in formats
  "html":       "...",                    // when "html" in formats
  "rawHtml":    "...",                    // when "rawHtml" in formats
  "links":      ["..."],                  // when "links" in formats
  "screenshot": "https://...",            // upload URL when screenshot requested
  "json":       { /* extracted */ },      // when typed {"type":"json", ...} format
  "metadata": {
    "title": "...", "sourceURL": "...", "url": "...", "statusCode": 200,
    "contentType": "...", "language": "...", "creditsUsed": 1,
    "cacheState": "hit"|"miss", "cachedAt": "ISO8601",
    "proxyUsed": "basic"|"stealth", "scrapeId": "..."
    // …plus any og:/twitter:/jsonLd fields the page exposes
  },
  "creditsUsed": 1,                       // top-level (= metadata.creditsUsed)
  "warning":     "..."                    // optional, upstream soft warning
}
```

## Pricing

- Base **1 fc-credit × 0.9** = **0.9 mulerun-credit** per successful call.
- Add-ons (server-side, reported via `creditsUsed`):
  - `formats: [{type:"json",...}]` (LLM extraction) — **+4**
  - `proxy: "stealth"` (Enhanced Mode) — **+4**
  - `parsers: [{type:"pdf"}]` — **+1 per PDF page**
  - `zeroDataRetention: true` — **+1**
- HTTP error / `success=false` (incl. 402 out-of-credit) — **not charged**.

## Errors

The skill exits non-zero and prints a JSON `{error, detail}` blob to
stderr on:
- Missing env (`FIRECRAWL_BASE_URL` / `FIRECRAWL_API_KEY`)
- HTTP error from mule-router (4xx/5xx)
- Network/timeout (180s)
- Invalid JSON in argument or response

| HTTP | Cause | Action |
|------|-------|--------|
| 4xx (422) | Bad payload (e.g. unsupported format value, missing `url`) | Fix the body and retry. |
| 402 | `subscription_required` / out-of-credit | **Stop**, fall back to `WebFetch`. |
| 5xx | Upstream Firecrawl transient | Retry **once** after short wait. |

## Examples

Basic markdown extraction:

```bash
python3 scripts/firecrawl-scrape.py '{"url":"https://example.com"}'
```

Main content only, with screenshot:

```bash
python3 scripts/firecrawl-scrape.py '{
  "url":            "https://docs.firecrawl.dev",
  "formats":        ["markdown", "screenshot"],
  "onlyMainContent": true
}'
```

JS-rendered SPA with a 3s render wait:

```bash
python3 scripts/firecrawl-scrape.py '{
  "url":     "https://example.com/spa",
  "waitFor": 3000
}'
```

Structured extraction via LLM (+4 credits):

```bash
python3 scripts/firecrawl-scrape.py '{
  "url":     "https://example.com/pricing",
  "formats": [{
    "type":   "json",
    "prompt": "Extract plan names and monthly prices as {name, price_usd}[]"
  }]
}'
```

PDF scrape (+1 credit per page):

```bash
python3 scripts/firecrawl-scrape.py '{
  "url":     "https://arxiv.org/pdf/2401.12345.pdf",
  "parsers": [{"type": "pdf", "mode": "auto", "maxPages": 50}]
}'
```

## Tips

- Prefer plain `markdown` over typed `{type:"json", prompt:...}` when
  you can grep the result yourself — saves 4 credits.
- For multi-page extraction, call this skill in a loop. There is no
  `crawl` / `map` skill yet (those Firecrawl endpoints aren't exposed
  via mule-router).
- Always quote URLs — `?` and `&` are shell-special.
