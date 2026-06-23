---
name: microsoft
description: Up-to-date Microsoft Graph API knowledge for AI agents. Search 27,700+ Graph APIs, endpoint docs, resource schemas, and community samples — all locally, no network calls. Then execute Graph calls directly using a token the platform has already injected. Use when the agent needs to find, understand, or call Microsoft Graph endpoints (SharePoint, OneDrive, Outlook mail/calendar, Teams, Entra, Intune, ...).
license: MIT
metadata:
  author: merill (upstream) + MuleRun fork (static-token auth)
  version: "1.0.19+static-token"
---

# Microsoft Graph Agent Skill

Search, look up, and call any of the 27,700+ Microsoft Graph APIs — all locally, no network calls needed. Use the three search commands to find the right endpoint, check permissions and parameters, then execute calls directly using the access token the enterprise platform has already injected.

## What's Included

The Microsoft Graph API has **27,700+ endpoints** updated weekly — well past LLM training cutoffs. This skill bundles the complete API surface as local indexes that you search instantly with no network calls.

| Index | Count | What it contains |
|---|---|---|
| OpenAPI endpoints | 27,700+ | Path, method, summary, description, permission scopes |
| Endpoint docs | 6,200+ | Permissions (delegated/app), query parameters, required headers, default vs `$select`-only properties |
| Resource schemas | 4,200+ | All properties with types, supported `$filter` operators, default/select-only flags |
| Community samples | Growing | Hand-verified queries mapping natural-language tasks to exact API calls |

## How to Run

The `msgraph` CLI is bundled with this skill and exposed on `PATH` (via
`/usr/local/bin/msgraph`) by `scripts/_install.sh` at install time. Simply call:

```
msgraph <subcommand> [args...]
```

The launcher (`scripts/msgraph`) sources this skill's `.env` so the
platform-injected access token (`MICROSOFT_ACCESS_TOKEN`, normalized to
`MSGRAPH_ACCESS_TOKEN`) reaches every invocation automatically.

## Finding the Right API

This is the primary purpose of the skill. Follow this progressive lookup strategy — each level adds detail:

1. **Your own knowledge** — try first for well-known endpoints (`/me`, `/users`, `/groups`).
2. **`sample-search`** — curated, hand-verified samples. Highest quality. Use for common tasks and multi-step workflows.
3. **`api-docs-search`** — per-endpoint permissions, supported query parameters, required headers, default vs `$select`-only properties, and resource property details with filter operators.
4. **`openapi-search`** — full catalog of 27,700 Graph APIs. Use when you cannot find the endpoint any other way.
5. **Reference files** — concept docs on query parameters, advanced queries, paging, batching, throttling, errors, and best practices. Read only when you need specific guidance.

This order is guidance — adapt based on the task. For example, jump straight to `api-docs-search` if you already know the endpoint but need its permissions.

### sample-search

Search curated community samples that map natural-language tasks to exact Microsoft Graph API queries:

```
msgraph sample-search --query "conditional access policies"
msgraph sample-search --product entra
msgraph sample-search --query "managed devices" --product intune
```

| Flag | Description |
|---|---|
| `--query` | Free-text search (searches intent and query fields) |
| `--product` | Filter by product: `entra`, `intune`, `exchange`, `teams`, `sharepoint`, `security`, `general` |
| `--limit` | Max results (default 10) |

At least one of `--query` or `--product` is required. Results include multi-step workflows.

### api-docs-search

Look up detailed documentation for a specific endpoint or resource type:

```
msgraph api-docs-search --endpoint /users --method GET
msgraph api-docs-search --resource user
msgraph api-docs-search --query "ConsistencyLevel"
```

| Flag | Description |
|---|---|
| `--endpoint` | Search by endpoint path (e.g. `/users`, `/me/messages`) |
| `--resource` | Search by resource type name (e.g. `user`, `group`, `message`) |
| `--method` | Filter by HTTP method: `GET`, `POST`, `PUT`, `PATCH` |
| `--query` | Free-text search across all fields |
| `--limit` | Max results (default 10) |

At least one of `--endpoint`, `--resource`, or `--query` is required.

**Endpoint results** include: required permissions (delegated work/school, delegated personal, application), supported OData query parameters, required headers, default properties, and endpoint-specific notes.

**Resource results** include: all properties with types, supported `$filter` operators (eq, ne, startsWith, etc.), and whether each property is returned by default or requires `$select`.

### openapi-search

Search the full OpenAPI catalog of 27,700 Microsoft Graph APIs:

```
msgraph openapi-search --query "send mail"
msgraph openapi-search --resource messages --method GET
```

| Flag | Description |
|---|---|
| `--query` | Free-text search (searches path, summary, description) |
| `--resource` | Filter by resource name (e.g. `users`, `groups`, `messages`) |
| `--method` | Filter by HTTP method |
| `--limit` | Max results (default 20) |

At least one of `--query`, `--resource`, or `--method` is required.

## Microsoft Graph API Execution

This skill executes Microsoft Graph API calls directly. The enterprise platform has already done the OAuth flow and injected the resulting access token into this skill's environment, so **no interactive sign-in is required or possible inside the sandbox**.

### Authentication

The token is read from environment variables, in this order:

1. `MSGRAPH_ACCESS_TOKEN` — set by this skill explicitly, takes priority.
2. `MICROSOFT_ACCESS_TOKEN` — set by the platform's Nango → credential-mapping pipeline (default for the `microsoft` provider).

When either is present, the CLI runs in **static-token mode** (`authMethod: static-token`): every `graph-call` sends the injected token as a bearer header; no MSAL, no token cache, no interactive flow.

**Quick check:**

```
msgraph auth status
```

A successful response looks like:

```json
{
  "authMethod": "static-token",
  "signedIn": true,
  "tokenSource": "injected (MSGRAPH_ACCESS_TOKEN / MICROSOFT_ACCESS_TOKEN)"
}
```

If `signedIn` is `false`, no token has been injected — the integration is not bound to this skill, or it has not been authorized yet. Have the user authorize the Microsoft integration in the platform UI; do NOT attempt `msgraph auth signin` (the sandbox has no browser and the token would not be honoured anyway).

The token's scopes are whatever was consented when the Microsoft integration was authorized in the platform (Entra App permissions + admin consent). The skill cannot widen them — request additional scopes by re-authorizing the integration with a wider Entra App configuration.

### Making Graph API Calls

**IMPORTANT**: Run `msgraph auth status` before the first `graph-call` in a session to verify a token is present.

```
msgraph graph-call <METHOD> <URL> [flags]
```

#### Read Operations

```
msgraph graph-call GET /me
msgraph graph-call GET /users --select "displayName,mail" --top 10
msgraph graph-call GET /me/messages --filter "isRead eq false" --top 5 --select "subject,from,receivedDateTime"
msgraph graph-call GET /users --filter "startsWith(displayName,'John')"
```

#### Write Operations

**IMPORTANT**: YOU MUST ask the user for confirmation before any write operation. Write operations require the `--allow-writes` flag.

```
msgraph graph-call POST /me/sendMail --body '{"message":{"subject":"Hello","body":{"content":"Hi"},"toRecipients":[{"emailAddress":{"address":"user@example.com"}}]}}' --allow-writes
msgraph graph-call PATCH /me --body '{"jobTitle":"Engineer"}' --allow-writes
```

**DELETE is always blocked** regardless of flags.

#### graph-call Flags

| Flag | Description | Example |
|---|---|---|
| `--select` | OData $select | `--select "displayName,mail"` |
| `--filter` | OData $filter | `--filter "isRead eq false"` |
| `--top` | OData $top (limit results) | `--top 10` |
| `--expand` | OData $expand | `--expand "members"` |
| `--orderby` | OData $orderby | `--orderby "displayName desc"` |
| `--api-version` | `v1.0` or `beta` (default: beta) | `--api-version v1.0` |
| `--headers` | Custom HTTP headers | `--headers "ConsistencyLevel:eventual"` |
| `--body` | Request body (JSON) | `--body '{"key":"value"}'` |
| `--output` | `json` (default) or `raw` | `--output raw` |
| `--allow-writes` | Allow POST/PUT/PATCH (requires user confirmation) | |

> Note: `--scopes` (incremental consent) is **not supported** in static-token mode — the scopes are fixed at the moment the integration was authorized. To get more scopes, re-authorize the integration with a wider Entra App.

## Known Pitfalls

LLM training data contains many Graph endpoints that have since been renamed,
removed, or never existed. Treat these as **landmines** — verify before calling.

| Wrong (don't call) | Symptom | Right call |
|---|---|---|
| `GET /me/teams` | 404 on both v1.0 and beta | `GET /me/joinedTeams` |
| `GET /me/drive/special/recent` | 400 (special folder not enumerable on org accounts) | `GET /me/drive/recent` |
| `$filter=endswith(name,'.docx')` on `/drive/.../children` | 400 — `driveItem` collection does not support `endswith()` | Drop the filter and filter client-side, **or** use `/me/drive/root/search(q='.docx')` |
| `Notes.Read` / OneNote endpoints with the default Microsoft App | 401 — token has no Notes scope | Add `Notes.Read` (or `Notes.ReadWrite`) to the Entra App, **Grant admin consent**, then re-authorize the integration so a fresh token with the wider scope is injected. The skill itself cannot add scopes. |

**Rule of thumb**: when in doubt, run `msgraph openapi-search --query "<keyword>"` or `msgraph api-docs-search --endpoint <path>` BEFORE the `graph-call`. The local indexes are zero-network and finish in milliseconds.

## Critical Rules

### Always (search and knowledge)

1. **Never guess or fabricate Microsoft Graph endpoints** — always verify via search before calling. This skill exists because agents hallucinate endpoints; use it.
2. **Use the progressive lookup strategy** — start with what you know, then sample-search, api-docs-search, openapi-search as needed.
3. **Use `--select`** to reduce response size — only request fields you need.
4. **Use `--top`** to limit results — avoid fetching thousands of records.
5. **ConsistencyLevel header** is required for `$count` and `$search` on directory objects (users, groups, etc.). Use `--headers "ConsistencyLevel:eventual"`.
6. **Default API version is beta** — use `--api-version v1.0` for production-stable endpoints.

### When using graph-call

7. **Check auth status** before the first `graph-call` in a session — confirms a token was injected.
8. **GET is the default** — no special flags needed.
9. **Write operations require `--allow-writes`** — YOU MUST confirm with the user first.
10. **DELETE is always blocked** — inform the user this is not supported.
11. **All output is JSON** — parse `statusCode` and `body` fields from the response.
12. **No interactive sign-in** — never run `auth signin` / `auth signout` inside the sandbox; the token comes from the platform, not from the CLI. A 401 means the injected token expired or was revoked.

## Error Handling

| Status | Meaning | Action |
|---|---|---|
| 401 | Injected token expired or revoked | Ask the user to re-authorize the Microsoft integration in the platform UI; the platform will inject a fresh token. Do NOT run `auth signin`. |
| 403 | Insufficient permissions | The integration's Entra App is missing the required Graph scope (or admin consent). Use `api-docs-search` to confirm the exact permission, then have the user add it to the Entra App and re-authorize the integration. |
| 404 | Resource not found | Verify the endpoint path with `openapi-search` / `api-docs-search`. |
| 429 | Rate limited | Wait for `Retry-After` duration, then retry. |

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `MSGRAPH_ACCESS_TOKEN` | Pre-issued bearer token (this fork). Takes priority. | — |
| `MICROSOFT_ACCESS_TOKEN` | Pre-issued bearer token (platform default env name). Fallback. | — |
| `MSGRAPH_API_VERSION` | Default API version | `beta` |
| `MSGRAPH_INDEX_DB_PATH` | Path to OpenAPI index database | Auto-detected |
| `MSGRAPH_SAMPLES_DB_PATH` | Path to samples index database | Auto-detected |
| `MSGRAPH_API_DOCS_DB_PATH` | Path to API docs index database | Auto-detected |

> `MSGRAPH_CLIENT_ID`, `MSGRAPH_TENANT_ID`, `MSGRAPH_CLIENT_SECRET`, `MSGRAPH_AUTH_METHOD`, `MSGRAPH_NO_TOKEN_CACHE`, etc. are honoured by the upstream CLI for non-sandbox use but are **ignored when a static token is injected**. In the MuleRun sandbox you do not need to set any of them.

## Compatibility

Search tools run fully offline with no network access required. Direct API execution requires network access to `graph.microsoft.com` (the injected token is used as-is; no calls to `login.microsoftonline.com`).

## Reference Files

Load these on demand when you need specific guidance. Do NOT load them preemptively.

| File | When to Read | Size |
|---|---|---|
| [references/REFERENCE.md](references/REFERENCE.md) | Common resource paths, OData patterns, permission scopes | ~230 lines |
| [references/docs/query-parameters.md](references/docs/query-parameters.md) | OData $select, $filter, $expand, $top, $orderby, $search syntax and gotchas | ~300 lines |
| [references/docs/advanced-queries.md](references/docs/advanced-queries.md) | ConsistencyLevel header, $count, $search, ne/not/endsWith on directory objects | ~190 lines |
| [references/docs/paging.md](references/docs/paging.md) | @odata.nextLink pagination, server-side vs client-side paging | ~50 lines |
| [references/docs/batching.md](references/docs/batching.md) | $batch endpoint, combining multiple requests, dependsOn sequencing | ~280 lines |
| [references/docs/throttling.md](references/docs/throttling.md) | 429 handling, Retry-After, backoff strategy | ~90 lines |
| [references/docs/errors.md](references/docs/errors.md) | HTTP status codes, error response format, error codes | ~105 lines |
| [references/docs/best-practices.md](references/docs/best-practices.md) | $select for performance, pagination, delta queries, batching | ~155 lines |

> The upstream `references/docs/authentication.md` is not relevant in this fork — the sandbox uses static-token injection only.
