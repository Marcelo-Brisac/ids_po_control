# Session Management

Multiple isolated browser sessions with state persistence and concurrent browsing.

**Related**: [authentication.md](authentication.md) for login patterns, [SKILL.md](../SKILL.md) for quick start.

## Contents

- [Named Sessions](#named-sessions)
- [Session Isolation Properties](#session-isolation-properties)
- [Session State Persistence](#session-state-persistence)
- [Common Patterns](#common-patterns)
- [Default Session](#default-session)
- [Session Cleanup](#session-cleanup)
- [Best Practices](#best-practices)

## Named Sessions

Use `REMOTE_AGENT_BROWSER_SESSION` env var to isolate browser contexts:

```bash
# Session 1: Authentication flow
REMOTE_AGENT_BROWSER_SESSION=auth agent-browser open https://app.example.com/login

# Session 2: Public browsing (separate cookies, storage)
REMOTE_AGENT_BROWSER_SESSION=public agent-browser open https://example.com

# Commands are isolated by session
REMOTE_AGENT_BROWSER_SESSION=auth agent-browser fill @e1 "user@example.com"
REMOTE_AGENT_BROWSER_SESSION=public agent-browser get text body
```

## Session Isolation Properties

Each session has independent:
- Cookies
- LocalStorage / SessionStorage
- IndexedDB
- Cache
- Browsing history
- Open tabs

## Session State Persistence

### Save Session State

```bash
# Save cookies, storage, and auth state
agent-browser state save /path/to/auth-state.json
```

### Load Session State

```bash
# Restore saved state
agent-browser state load /path/to/auth-state.json

# Continue with authenticated session
agent-browser open https://app.example.com/dashboard
```

### State File Contents

```json
{
  "cookies": [...],
  "localStorage": {...},
  "sessionStorage": {...},
  "origins": [...]
}
```

## Common Patterns

### Authenticated Session Reuse

```bash
#!/bin/bash
# Save login state once, reuse many times

STATE_FILE="/tmp/auth-state.json"

# Check if we have saved state
if [[ -f "$STATE_FILE" ]]; then
    agent-browser state load "$STATE_FILE"
    agent-browser open https://app.example.com/dashboard
else
    # Perform login
    agent-browser open https://app.example.com/login
    agent-browser snapshot -i
    agent-browser fill @e1 "$USERNAME"
    agent-browser fill @e2 "$PASSWORD"
    agent-browser click @e3
    agent-browser wait --load networkidle

    # Save for future use
    agent-browser state save "$STATE_FILE"
fi
```

### Concurrent Scraping

```bash
#!/bin/bash
# Scrape multiple sites concurrently

# Start all sessions
REMOTE_AGENT_BROWSER_SESSION=site1 agent-browser open https://site1.com &
REMOTE_AGENT_BROWSER_SESSION=site2 agent-browser open https://site2.com &
REMOTE_AGENT_BROWSER_SESSION=site3 agent-browser open https://site3.com &
wait

# Extract from each
REMOTE_AGENT_BROWSER_SESSION=site1 agent-browser get text body > site1.txt
REMOTE_AGENT_BROWSER_SESSION=site2 agent-browser get text body > site2.txt
REMOTE_AGENT_BROWSER_SESSION=site3 agent-browser get text body > site3.txt

# Cleanup
REMOTE_AGENT_BROWSER_SESSION=site1 agent-browser close
REMOTE_AGENT_BROWSER_SESSION=site2 agent-browser close
REMOTE_AGENT_BROWSER_SESSION=site3 agent-browser close
```

### A/B Testing Sessions

```bash
# Test different user experiences
REMOTE_AGENT_BROWSER_SESSION=variant-a agent-browser open "https://app.com?variant=a"
REMOTE_AGENT_BROWSER_SESSION=variant-b agent-browser open "https://app.com?variant=b"

# Compare
REMOTE_AGENT_BROWSER_SESSION=variant-a agent-browser screenshot /tmp/variant-a.png
REMOTE_AGENT_BROWSER_SESSION=variant-b agent-browser screenshot /tmp/variant-b.png
```

## Default Session

When `REMOTE_AGENT_BROWSER_SESSION` is not set, commands use the default session:

```bash
# These use the same default session
agent-browser open https://example.com
agent-browser snapshot -i
agent-browser close  # Closes default session
```

## Session Cleanup

```bash
# Close specific session
REMOTE_AGENT_BROWSER_SESSION=auth agent-browser close

# List active sessions
agent-browser session list
```

## Best Practices

### 1. Name Sessions Semantically

```bash
# GOOD: Clear purpose
REMOTE_AGENT_BROWSER_SESSION=github-auth agent-browser open https://github.com
REMOTE_AGENT_BROWSER_SESSION=docs-scrape agent-browser open https://docs.example.com

# AVOID: Generic names
REMOTE_AGENT_BROWSER_SESSION=s1 agent-browser open https://github.com
```

### 2. Always Clean Up

```bash
# Close sessions when done
REMOTE_AGENT_BROWSER_SESSION=auth agent-browser close
REMOTE_AGENT_BROWSER_SESSION=scrape agent-browser close
```

### 3. Handle State Files Securely

```bash
# Don't commit state files (contain auth tokens!)
echo "*.auth-state.json" >> .gitignore

# Delete after use
rm /tmp/auth-state.json
```

### 4. Timeout Long Sessions

```bash
# Set timeout for automated scripts
timeout 60 agent-browser get text body
```
