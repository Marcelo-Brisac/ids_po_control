---
name: x-search
description: Search recent public X (Twitter) posts from the last 7 days. Use when looking up tweets, X discussions, posts by a handle, or posts containing specific keywords / hashtags / cashtags — either at the user's explicit request, or when X is a useful source for the task at hand.
---

# X (Twitter) Search Recent

```bash
python3 scripts/x-search.py '<json_body>'
```

JSON body is the upstream `POST /v1/search-recent` request body.
Prints per-post summary: handle, ISO timestamp, lang, engagement
(`likes=N rt=N reply=N views=N`), text, post URL, plus header
`Results: N` and `next_token=...` when more pages exist. Full upstream
JSON saved to `/tmp/x_search_<pid>.json`.

Script auto-sets these on the body (override by passing the key):

```jsonc
{
  "tweet_fields": ["created_at", "public_metrics", "lang"],
  "expansions":   ["author_id"],
  "user_fields":  ["username", "name", "verified"]
}
```

Script also auto-injects noise filters into `query` (each suppressed if
the caller already mentions the relevant operator):

| Auto-injected | Suppressed when query contains |
|---|---|
| `-is:reply` | `is:reply` |
| `min_likes:1` | `min_likes:` |
| `min_replies:1` | `min_replies:` |
| `lang:en` (only if query is ASCII) | any `lang:` |

The actual sent query is echoed as `[auto-filters added: ...]`.

## Request body

| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| `query` | string | ✅ | — | length 1..4096; X operator grammar (see below) |
| `max_results` | int | — | `10` | **10..100** (floor is 10, not 1) |
| `start_time` | ISO 8601 UTC | — | — | seconds; inclusive; **must be within the last 7 days** |
| `end_time` | ISO 8601 UTC | — | — | seconds; exclusive |
| `since_id` | string | — | — | 1..19 digits; posts newer than this |
| `until_id` | string | — | — | 1..19 digits; posts older than this |
| `sort_order` | enum | — | `relevancy` | `recency` \| `relevancy` |
| `next_token` | string | — | — | from previous response's `meta.next_token` |
| `tweet_fields` / `expansions` / `media_fields` / `poll_fields` / `user_fields` / `place_fields` | list[string] | — | (auto for first three) | see [references/api.md](references/api.md) for common values |

## Operators in `query`

- `from:<handle>` — by author (no `@`)
- `to:<handle>` — replies to author
- `-is:retweet`, `-is:reply`, `-is:nullcast` — exclude retweets / replies / promoted-ad posts
- `min_likes:N`, `min_replies:N` — minimum engagement (server-side, no over-fetch)
- `lang:<bcp47>` — language filter (`lang:en`, `lang:zh`, …)
- `has:media`, `has:links`, `has:videos` — content filters
- `place:<id>` — location filter
- `#<tag>`, `$<cashtag>` — hashtag / cashtag
- `OR`, `()` — boolean grouping
- `"exact phrase"` — quote multi-word terms

❌ **Do not use**:
- `min_faves:N`, `min_retweets:N` — Standard/Premium operators, this v2
  endpoint rejects them with HTTP 500. Use `min_likes:N` instead.
- `"phrase * wildcard"` — silently ignored, treated as `"phrase wildcard"`.

## Error Handling

If a call fails with `"Subscription required"` (HTTP 402), **stop using this skill entirely** and try fulfilling the request with web search or other tools instead. Also call `suggest_subscription` with feature `x-search` so the user sees a subscription hint.

## Errors

Body shape: `{"status":N,"title":"...","detail":"...","instance":"...","error_code":N}`.

| HTTP | `error_code` | Cause |
|------|--------------|-------|
| `422` | (validation) | Bad payload (`max_results<10`, empty `query`, `start_time` > 7d, bad ID digits). Fix the body. |
| `423` | `insufficient_balance` | Out of credit. **Stop, fall back, do not retry.** |
| `402` | `subscription_required` | Plan does not include this tool. See Error Handling above. |
| `5xx` | `3001` / `3002` / `3004` / `3006` | Transient upstream failure. Retry **once** after a short wait. |
| `5xx` | other `error_code` | Permanent — do not retry. |

Response may also be HTTP 200 with a populated `errors` list alongside
`data` — per-resource partial failures. Inspect both before reporting
"no results".

## Pricing

`max(1, result_count × 0.5)` credit per successful call. Empty result
costs the floor of 1 credit. Failures (non-2xx, validation, network)
cost nothing.

## Examples

Newest takes on a model:

```bash
python3 scripts/x-search.py '{
  "query": "\"Claude 4.6\" -is:retweet",
  "max_results": 30,
  "sort_order": "recency"
}'
```

Two specific accounts:

```bash
python3 scripts/x-search.py '{
  "query": "(from:OpenAI OR from:sama) -is:retweet",
  "max_results": 20,
  "sort_order": "recency"
}'
```

A specific window inside the 7-day budget:

```bash
python3 scripts/x-search.py '{
  "query": "gpt-5 lang:en -is:retweet",
  "start_time": "2026-05-25T00:00:00Z",
  "end_time":   "2026-05-28T00:00:00Z",
  "max_results": 50
}'
```

Pagination:

```bash
python3 scripts/x-search.py '{
  "query":       "openai -is:retweet",
  "max_results": 100,
  "sort_order":  "recency",
  "next_token":  "b26v89c19zqg8o3..."
}'
```

For the full response schema (`Post`, `includes`, `meta`,
`ErrorObject`), list-field common values, and the `pagination_token`
alias, see [references/api.md](references/api.md).
