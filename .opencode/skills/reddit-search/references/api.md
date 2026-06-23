# Reddit Search Posts — API reference

Full schema for `POST $REDDIT_SEARCH_BASE_URL/v1/search-posts`. The
skill's `scripts/reddit-search.py` wrapper takes the same JSON body as
`-d`, so every field below applies as a top-level key in the body
argument.

## Request body

| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| `query` | string | ✅ | — | length 1..512. Keyword(s). Reddit operators accepted (see [Operators](#operators)). |
| `subreddit` | string | — | — | max length 128. Subreddit name **without** the `r/` prefix (e.g. `OpenAI`, not `r/OpenAI`). |
| `sort` | enum | — | upstream `relevance` | `relevance` \| `hot` \| `top` \| `new` \| `comments`. |
| `time` | enum | — | — | `hour` \| `day` \| `week` \| `month` \| `year` \| `all`. **Only valid when `sort="top"`.** Other combinations are rejected with HTTP 422. |
| `cursor` | string | — | — | Pagination cursor from previous response's `data.cursor`. |

### Operators

Accepted inside `query`:

- `title:<word>` — match in title only
- `author:<user>` — by username (no `u/`)
- `selftext:<word>` — match in body text
- `flair:<text>` — match post flair
- `site:<domain>` — link posts to a specific domain
- `self:yes` — self-posts only
- `nsfw:no` — exclude NSFW
- Standard boolean: `AND`, `OR`, `NOT`, parentheses, quotes for phrases

### `time` × `sort` constraint

```jsonc
{ "query": "openai", "sort": "top", "time": "week" }   // valid
{ "query": "openai", "sort": "top" }                   // valid (time omitted)
{ "query": "openai", "time": "week" }                  // 422 (sort not "top")
{ "query": "openai", "sort": "new", "time": "day" }    // 422
```

## Response schema

HTTP 200 JSON body.

| Field | Type | Always present | Description |
|-------|------|----------------|-------------|
| `success` | bool (always `true`) | ✅ | Business-success flag. Upstream `success=false` responses are converted to HTTP 4xx. |
| `data`    | object               | ✅ | Page payload, see below. |

### `data`

| Field | Type | Always present | Description |
|-------|------|----------------|-------------|
| `cursor` | string \| null | sometimes absent | Pass back as `cursor` in the next request to fetch the next page. Absent or empty string on the last page. |
| `posts`  | list[Thing]    | ✅ (may be empty) | Page of post Things. |

### `Thing` (item of `data.posts`)

| Field | Type | Always present | Description |
|-------|------|----------------|-------------|
| `kind` | string | ✅ | Always `"t3"` for this endpoint (Reddit Thing kind = link/post). Comments (`t1`), accounts (`t2`), subreddits (`t5`), etc. are not returned. |
| `data` | object | ✅ | Post fields. Loosely typed passthrough (~111 fields, evolves over time); read defensively. Common fields below. |

### Common fields in `Thing.data`

| Field | Type | Description |
|-------|------|-------------|
| `id`              | string | Reddit base-36 post ID (used to build `t3_<id>` Thing fullname). |
| `name`            | string | Thing fullname (e.g. `t3_1ax2y3z`). |
| `title`           | string | Post title. |
| `author`          | string | Author username (no `u/` prefix). |
| `subreddit`      | string | Subreddit name (no `r/` prefix). |
| `subreddit_id`    | string | Subreddit Thing fullname (e.g. `t5_2qh1i`). |
| `score`           | int    | Net score (ups − downs). |
| `ups`             | int    | Upvote count. |
| `downs`           | int    | Downvote count. |
| `upvote_ratio`    | float  | 0.0..1.0. |
| `num_comments`    | int    | Top-level + nested comment count. |
| `created_utc`     | float  | Unix epoch seconds (UTC). |
| `url`             | string | Linked URL (== `permalink` for self-posts). |
| `permalink`       | string | `/r/<sub>/comments/<id>/<slug>/` — prepend `https://www.reddit.com` for the full URL. |
| `selftext`        | string | Body text for self-posts; empty for link posts. |
| `selftext_html`   | string \| null | HTML-rendered selftext. |
| `is_self`         | bool   | True if self-post (no external link). |
| `is_video`        | bool   | True if Reddit-native video. |
| `over_18`         | bool   | NSFW flag. |
| `spoiler`         | bool   | Spoiler flag. |
| `locked`          | bool   | Comments locked. |
| `stickied`        | bool   | Pinned in subreddit. |
| `thumbnail`       | string | Thumbnail URL, or sentinel (`self`, `default`, `nsfw`, `image`). |
| `link_flair_text` | string \| null | Post flair. |
| `author_flair_text` | string \| null | Author's flair in this subreddit. |
| `domain`          | string | Domain of linked URL (e.g. `self.OpenAI`, `i.redd.it`, `youtube.com`). |
| `media`           | object \| null | Embedded media metadata. |
| `preview`         | object \| null | Image / video preview info. |

## Error codes

Error body shape: `{"status":N,"title":"...","detail":"...","instance":"...","error_code":N}`.

| HTTP | `error_code` | Cause |
|------|--------------|-------|
| `422` | (validation) | Payload violates the schema. Most common: `time` set with `sort != "top"`. Also: empty `query`, `query > 512` chars, `subreddit` with `r/` prefix or > 128 chars. |
| `423` | `insufficient_balance` | Caller balance below 9.8 credit. |
| `402` | `subscription_required` | Plan does not include this tool. |
| `5xx` | `3001` / `3002` / `3004` / `3006` | Transient upstream failure. Retry **once** after a short wait. |
| `5xx` | other `error_code` | Permanent — do not retry. |

## Pricing

**Flat 9.8 credit per successful call.** Independent of the number of
posts returned (0 hits cost the same as 100). Failures (non-2xx,
`success=false`, validation, network) cost nothing.
