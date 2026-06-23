---
name: mulerun-shared
description: "MuleRun CLI: Global flags, security rules, and output conventions"
---

# MuleRun CLI — Shared Configuration

> This skill is a **prerequisite** for all other mulerun-* skills.
> Run `mulerun --help` to discover all available commands and subcommands.

## Agent Text Output Rules (CRITICAL — READ FIRST)

**The `mulerun` CLI is an internal tool. Users must NEVER know it exists.**

All `bash` code blocks in this and other mulerun-* SKILL.md files are
**internal execution references for YOU only**. They tell you what to run
behind the scenes — NEVER copy, quote, or paraphrase them to the user.

### Rules

- NEVER show CLI command names, flags, syntax, or raw output to the user
- NEVER mention "mulerun", "CLI", "schedule logs", or any subcommand name
- NEVER show task IDs, run IDs, cron expressions, or millisecond intervals
- Present all results in natural, conversational language
- When an operation fails, explain in plain language; do not paste error output

### Good vs Bad Examples

| Situation | BAD (leaks internals) | GOOD (natural language) |
|-----------|----------------------|------------------------|
| Task created | "Created. View logs with `mulerun computer schedule logs task-xxx`" | "All set! It will run every minute. I'll stop it for you after 5 minutes." |
| Show tasks | Raw CLI table output | "You have 2 scheduled tasks: 1) Weather check (every minute) 2) DB backup (daily at 11pm)" |
| Task failed | "exit code 1, stderr: connection timeout" | "The last run failed — looks like a network timeout. Want me to retry?" |
| Pause task | "Run `mulerun computer schedule update <id> --status paused`" | "Done, I've paused that task for you." |

The user interacts with an AI assistant, not a terminal.

## Security
- NEVER expose tokens in output
- All tokens are auto-managed; do not hardcode
- **Always** confirm with the user before executing destructive commands (e.g. `delete`, `cancel`)

## User Info
- `mulerun user me` — Get current user info
- `mulerun user balance` — Get user balance

## Global Flags
| Flag | Default | Description |
|------|---------|-------------|
| `--base-url` | — | API base URL |
| `-t, --token` | — | Authorization token |
| `-o, --output` | text | Output format: text, json, jsonl, table |
| `--proxy` | — | Proxy URL |
| `--debug` | false | Enable debug logging |
| `--timeout` | 30m | Operation timeout |
| `--no-color` | false | Disable terminal colors |

## Output Conventions
- stdout: data output (pipe-friendly)
- stderr: progress, status messages, errors
- Exit 0 = success, Exit 1 = error
- Use `-o json` for machine-readable output

## Error Codes
| Code | Meaning |
|------|---------|
| 401 | Token expired/invalid — login again |
| 403 | Insufficient permissions / feature not available for this plan |
| 404 | Resource not found |
| 409 | Resource conflict |
| 429 | Rate limited — retry after delay |
