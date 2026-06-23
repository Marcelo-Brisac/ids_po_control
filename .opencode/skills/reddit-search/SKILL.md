---
name: reddit-search
description: Search public Reddit posts by keyword, optionally scoped to one subreddit. Use when looking up Reddit discussions, posts in a specific subreddit, community sentiment on a topic, or the top / newest / most-commented posts matching a query — either at the user's explicit request, or when Reddit is a useful source for the task at hand.
---

# Reddit Search Posts

```bash
python3 scripts/reddit-search.py '<json_body>'
```

JSON body is the upstream `POST /v1/search-posts` request body.
Prints per-post summary: flair, title, subreddit, author, date,
`score=N comments=N`, selftext (full body for self-posts) or link
target (for link posts), plus header `Results: N` and `cursor=...`
when more pages exist. Full upstream JSON saved to
`/tmp/reddit_search_<pid>.json`.

This API is keyword search — `query` is required even when `subreddit`
is set.

## Request body

| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| `query` | string | ✅ | — | length 1..512; Reddit operator grammar (see below) |
| `subreddit` | string | — | — | max 128; **no `r/` prefix** (e.g. `OpenAI`, not `r/OpenAI`) |
| `sort` | enum | — | upstream `relevance` | `relevance` \| `hot` \| `top` \| `new` \| `comments` |
| `time` | enum | — | — | `hour` \| `day` \| `week` \| `month` \| `year` \| `all`. **Only valid when `sort="top"`** — any other combination → HTTP 422. |
| `cursor` | string | — | — | from previous response's `data.cursor` |

## Operators in `query`

- `title:<word>` — title only
- `author:<user>` — by username (no `u/`)
- `selftext:<word>` — body text
- `flair:<text>` — post flair
- `site:<domain>` — link posts to a specific domain
- `self:yes` — self-posts only
- `nsfw:no` — exclude NSFW
- Boolean: `AND`, `OR`, `NOT`, parentheses, `"exact phrase"`

## Error Handling

If a call fails with `"Subscription required"` (HTTP 402), **stop using this skill entirely** and try fulfilling the request with web search or other tools instead. Also call `suggest_subscription` with feature `reddit-search` so the user sees a subscription hint.

## Errors

Body shape: `{"status":N,"title":"...","detail":"...","instance":"...","error_code":N}`.

| HTTP | `error_code` | Cause |
|------|--------------|-------|
| `422` | (validation) | Bad payload. Most common: `time` with `sort != "top"`. Also: empty `query`, `query > 512` chars, `subreddit` with `r/` prefix. Fix the body. |
| `423` | `insufficient_balance` | Out of credit. **Stop, fall back, do not retry.** |
| `402` | `subscription_required` | Plan does not include this tool. See Error Handling above. |
| `5xx` | `3001` / `3002` / `3004` / `3006` | Transient upstream failure. Retry **once** after a short wait. |
| `5xx` | other `error_code` | Permanent — do not retry. |

HTTP 200 with `data.posts: []` is a legitimate empty result, not an
error.

## Pricing

**Flat 9.8 credit per successful call.** Independent of result count
(0 hits and 100 hits cost the same). Failures cost nothing.

## Examples

Top of the past week in r/OpenAI:

```bash
python3 scripts/reddit-search.py '{
  "query":     "openai",
  "subreddit": "OpenAI",
  "sort":      "top",
  "time":      "week"
}'
```

Subreddit-scoped, newest first:

```bash
python3 scripts/reddit-search.py '{
  "query":     "gpt-5",
  "subreddit": "OpenAI",
  "sort":      "new"
}'
```

Keyword across all of Reddit, by relevance:

```bash
python3 scripts/reddit-search.py '{
  "query": "\"vector database\" benchmark",
  "sort":  "relevance"
}'
```

Pagination:

```bash
python3 scripts/reddit-search.py '{
  "query":     "openai",
  "subreddit": "OpenAI",
  "sort":      "top",
  "time":      "month",
  "cursor":    "t3_1ax2y3z"
}'
```

For the full `Thing.data` field list (~25 commonly-used fields out of
~111), the `kind="t3"` semantics, and the full upstream response
schema, see [references/api.md](references/api.md).
