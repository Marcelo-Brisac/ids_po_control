---
name: mem-manage
description: Inspect, update, or delete entries in the user's persistent memory. Use when the user explicitly asks to review, change, or forget what is remembered about them — for example "what do you remember about me?", "update my preferred timezone to PST", or "forget that I work at Acme". Do NOT use for routine storing or recall — those are handled automatically and via the `mem_store` / `mem_recall` tools.
---

# Mem Manage

Manage persistent memories that mem9 has stored for the current user. The
authoritative tools for the hot path are:

- Automatic recall (every prompt) — handled by the platform.
- `mem_store` MCP tool — agent saves a new fact.
- `mem_recall` MCP tool — agent searches by query.

This skill covers the rarer management operations: list, get-by-id, update,
and delete. All operations talk directly to the mem9 REST API via `curl`.

## Prerequisites

Two environment variables must be set in the sandbox (provisioned by
session-mgmt — do not write them yourself):

- `MEM9_API_KEY` — per-user API key.
- `MEM9_API_URL` — mem9 REST base URL (defaults to `https://api.mem9.ai`).

If `MEM9_API_KEY` is empty, mem9 is not available in this environment. Tell
the user and stop.

```bash
: "${MEM9_API_URL:=https://api.mem9.ai}"
test -n "$MEM9_API_KEY" || { echo "Mem9 not configured"; exit 1; }
```

All requests below assume those vars are exported and use the same headers:

```bash
HDR_KEY="X-API-Key: $MEM9_API_KEY"
HDR_AGENT="X-Mnemo-Agent-Id: mule-agent"
HDR_JSON="Content-Type: application/json"
```

## Operations

### 1. List recent memories

```bash
curl -sf --max-time 8 \
  -H "$HDR_KEY" -H "$HDR_AGENT" -H "$HDR_JSON" \
  "${MEM9_API_URL%/}/v1alpha2/mem9s/memories?limit=20&offset=0"
```

Returns a JSON object `{ memories, total, limit, offset }`. Each memory has
an `id`, `content`, optional `tags`, `memory_type`, and `relative_age`.

### 2. Search by tag, type, or text

```bash
# By query
curl -sf --max-time 8 \
  -H "$HDR_KEY" -H "$HDR_AGENT" -H "$HDR_JSON" \
  "${MEM9_API_URL%/}/v1alpha2/mem9s/memories?q=$(printf %s "QUERY" | jq -sRr @uri)&limit=10"

# By tag (comma-separated)
curl -sf --max-time 8 \
  -H "$HDR_KEY" -H "$HDR_AGENT" -H "$HDR_JSON" \
  "${MEM9_API_URL%/}/v1alpha2/mem9s/memories?tags=preference,timezone"
```

### 3. Get a single memory by id

```bash
MEMORY_ID="..."
curl -sf --max-time 8 \
  -H "$HDR_KEY" -H "$HDR_AGENT" -H "$HDR_JSON" \
  "${MEM9_API_URL%/}/v1alpha2/mem9s/memories/${MEMORY_ID}"
```

### 4. Update a memory

```bash
MEMORY_ID="..."
curl -sf --max-time 8 -X PUT \
  -H "$HDR_KEY" -H "$HDR_AGENT" -H "$HDR_JSON" \
  -d '{"content":"NEW SENTENCE","tags":["preference"]}' \
  "${MEM9_API_URL%/}/v1alpha2/mem9s/memories/${MEMORY_ID}"
```

Only the fields you include are changed. Omit `tags` to leave them as-is.

### 5. Delete a memory

```bash
MEMORY_ID="..."
curl -sf --max-time 8 -X DELETE \
  -H "$HDR_KEY" -H "$HDR_AGENT" \
  "${MEM9_API_URL%/}/v1alpha2/mem9s/memories/${MEMORY_ID}"
```

A successful delete returns HTTP 204 with no body. A 404 means the id was
already gone.

## Workflow guidance

- **List or search first** to find the memory id — never ask the user to
  paste an id.
- **Show the memory content** to the user before destructive changes.
- **Confirm** updates and deletes when the user's request is ambiguous.
- **Do not print API keys** in any output you show the user.
- If a request fails, report the HTTP status and a short explanation. Do not
  retry blindly.
