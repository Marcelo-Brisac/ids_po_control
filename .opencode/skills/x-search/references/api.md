# X (Twitter) Search Recent — API reference

Full schema for `POST $X_SEARCH_BASE_URL/v1/search-recent`. The skill's
`scripts/x-search.py` wrapper takes the same JSON body as `-d`, so every
field below applies as a top-level key in the body argument.

## Request body

| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| `query` | string | ✅ | — | length 1..4096. Search expression in X operator grammar (see [Operators](#operators)). |
| `max_results` | int | — | `10` | **10..100** (floor is 10, not 1). |
| `start_time` | ISO 8601 UTC string | — | — | Seconds granularity. Inclusive lower bound. **Must fall inside the last 7 days.** |
| `end_time` | ISO 8601 UTC string | — | — | Seconds granularity. Exclusive upper bound. |
| `since_id` | string | — | — | 1..19 digits. Return only posts with ID greater than this (newer). |
| `until_id` | string | — | — | 1..19 digits. Return only posts with ID less than this (older). |
| `sort_order` | enum | — | `relevancy` | `recency` \| `relevancy`. |
| `next_token` | string | — | — | Pagination cursor from previous response's `meta.next_token`. |
| `pagination_token` | string | — | — | Alias of `next_token`. |
| `tweet_fields` | list[string] | — | — | Extra fields on each Post object. |
| `expansions` | list[string] | — | — | Referenced objects to expand into `includes`. |
| `media_fields` | list[string] | — | — | Extra fields on Media objects (requires `expansions=["attachments.media_keys"]`). |
| `poll_fields` | list[string] | — | — | Extra fields on Poll objects (requires `expansions=["attachments.poll_ids"]`). |
| `user_fields` | list[string] | — | — | Extra fields on User objects (requires `expansions=["author_id"]`). |
| `place_fields` | list[string] | — | — | Extra fields on Place objects (requires `expansions=["geo.place_id"]`). |

Both snake (`tweet_fields`) and dotted-alias (`tweet.fields`) names are
accepted. List fields take a JSON array; the server serializes to the
wire format.

### Operators

Accepted inside `query`:

- `from:<user>` — posts by a handle (no `@`)
- `to:<user>` — replies to a handle
- `-is:retweet`, `-is:reply` — exclude retweets / replies
- `lang:<bcp47>` — restrict by language (`lang:en`, `lang:zh`, …)
- `has:media`, `has:links`, `has:videos` — content filters
- `place:<id>` — location filter
- `#<tag>`, `$<cashtag>` — hashtag / cashtag
- `OR`, `()` — boolean grouping
- Quote phrases: `"exact phrase"`

### Common values for list-typed fields

| Field | Common values |
|-------|---------------|
| `tweet_fields` | `created_at`, `public_metrics`, `lang`, `conversation_id`, `author_id`, `referenced_tweets`, `attachments`, `entities`, `context_annotations`, `possibly_sensitive`, `source` |
| `expansions`   | `author_id`, `referenced_tweets.id`, `attachments.media_keys`, `attachments.poll_ids`, `geo.place_id`, `in_reply_to_user_id` |
| `media_fields` | `url`, `preview_image_url`, `type`, `duration_ms`, `width`, `height`, `alt_text` |
| `poll_fields`  | `duration_minutes`, `end_datetime`, `voting_status`, `options` |
| `user_fields`  | `name`, `username`, `verified`, `profile_image_url`, `public_metrics`, `description`, `created_at`, `location` |
| `place_fields` | `full_name`, `country`, `country_code`, `geo`, `place_type` |

### Script defaults

`scripts/x-search.py` auto-sets these on the body unless the caller
overrides them:

```jsonc
{
  "tweet_fields": ["created_at", "public_metrics", "lang"],
  "expansions":   ["author_id"],
  "user_fields":  ["username", "name", "verified"]
}
```

Passing your own value for any of these keys replaces the default — it
does not merge.

## Response schema

HTTP 200 JSON body. All top-level fields are optional.

| Field | Type | Description |
|-------|------|-------------|
| `data`     | list[Post]        | Posts. Omitted when no results. |
| `errors`   | list[ErrorObject] | Per-resource partial errors. Response is still 200. Inspect alongside `data` before reporting "no results". |
| `includes` | object            | Joined objects (present when `expansions` was used). |
| `meta`     | object            | Pagination + counts. |

### `Post` (item of `data`)

| Field | Type | Present when |
|-------|------|--------------|
| `id`                 | string                | always (19-digit Post ID) |
| `text`               | string                | always |
| `created_at`         | ISO 8601 string       | `tweet_fields` includes it |
| `lang`               | string (BCP-47)       | requested |
| `author_id`          | string                | requested; join to `includes.users[*].id` |
| `conversation_id`    | string                | requested; root Post ID of the thread |
| `public_metrics`     | object                | requested. Keys: `retweet_count`, `reply_count`, `like_count`, `quote_count`, `bookmark_count`, `impression_count` |
| `referenced_tweets`  | list[object]          | requested. Items: `{ type: "retweeted" \| "quoted" \| "replied_to", id }` |
| `attachments`        | object                | requested. Keys: `media_keys?`, `poll_ids?` |
| `entities`           | object                | requested. URLs / hashtags / mentions / cashtags extracted from `text` |
| `context_annotations`| list[object]          | requested. Topic / entity annotations |
| `possibly_sensitive` | bool                  | requested |
| `source`             | string                | requested. Client app that posted (deprecated by X — may be empty) |

### `includes` (present when `expansions` used)

| Field | Type | Notes |
|-------|------|-------|
| `users`  | list[User]  | Resolved authors / mentioned users. Minimum fields `id`, `name`, `username`, plus any `user_fields` requested. |
| `tweets` | list[Post]  | Resolved referenced (quoted / retweeted / replied_to) tweets. |
| `media`  | list[Media] | Minimum fields `media_key`, `type`, plus any `media_fields` requested. |
| `polls`  | list[Poll]  | |
| `places` | list[Place] | |

### `meta`

| Field | Type | Present when |
|-------|------|--------------|
| `result_count` | int    | always — drives billing |
| `newest_id`    | string | results exist; largest Post ID in `data` |
| `oldest_id`    | string | results exist; smallest Post ID in `data` |
| `next_token`   | string | more pages exist — pass back as `next_token`; stop when absent |

### `ErrorObject` (item of `errors`)

| Field | Description |
|-------|-------------|
| `title`         | Short error label, e.g. `Not Found Error`. |
| `detail`        | Human-readable explanation. |
| `type`          | URI identifying the error class. |
| `resource_type` | e.g. `tweet`, `user`. |
| `parameter`     | Which input caused the error. |
| `value`         | Offending value. |

## Error codes

Error body shape: `{"status":N,"title":"...","detail":"...","instance":"...","error_code":N}`.

| HTTP | `error_code` | Cause |
|------|--------------|-------|
| `422` | (validation) | Payload violates the schema (`max_results<10`, empty `query`, bad `since_id`/`until_id`, `start_time` > 7d, etc.). |
| `423` | `insufficient_balance` | Caller balance below 1 credit. |
| `402` | `subscription_required` | Plan does not include this tool. |
| `5xx` | `3001` / `3002` / `3004` / `3006` | Transient upstream failure. Retry **once** after a short wait. |
| `5xx` | other `error_code` | Permanent — do not retry. |

## Pricing

`max(1, result_count × 0.5)` credit per successful call. Empty result
still costs 1 credit (floor). Failures (non-2xx, validation, network)
cost nothing.
