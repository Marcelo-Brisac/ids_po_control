---
name: remote-agent-browser
description: |
  Browser automation via the user's own browser. Load this skill for any browser or web interaction task — navigating pages, filling forms, clicking elements, taking screenshots, extracting data, or testing web apps. When the user rejects authorization or My Browser is unavailable, fall back to the ../playwright-cli skill for cloud browser.
---

# Browser Automation with remote-agent-browser

The CLI connects to a **remote browser** via a gateway service using CDP. It is command-compatible with agent-browser but operates through a remote gateway instead of a local daemon.

## Prerequisites

- A JWT token for authentication (`--token` or `REMOTE_AGENT_BROWSER_TOKEN`)
- Access to the browser gateway (default: `http://localhost:8090`)
- The browser extension installed on the user's machine for session authorization

## Gateway Connection & Browser Selection

### Selecting a Remote Browser

When only one browser is enabled, it is selected automatically. When **multiple browsers are enabled** and no `--browser` is specified, the gateway returns a `CONFLICT` error.

**Multi-browser workflow:**

1. List available browsers:

```bash
remote-agent-browser --token <jwt> browser list
```

2. If multiple **enabled** browsers are returned, you **MUST call askuserquestion** to let the user choose which browser to use. Use each browser's name as an option label. **Never pick a browser yourself** — always let the user decide.

3. Pass the chosen browser ID with `--browser` and proceed with the authorization flow. If authorization is rejected, switch to Playwright CLI directly — do not ask the user to pick another browser.

```bash
remote-agent-browser --token <jwt> --browser <browser-id> open https://example.com
```

The `--browser` flag must be included on **every command invocation** (or set via `REMOTE_AGENT_BROWSER_BROWSER`). If the browser ID changes between invocations, the daemon automatically reconnects to the new browser.

```bash
# Select browser via flag
remote-agent-browser --token <jwt> --browser <browser-id> open https://example.com

# Via environment variable
export REMOTE_AGENT_BROWSER_BROWSER=<browser-id>
remote-agent-browser --token <jwt> open https://example.com
```

### Output Mode

JSON output is **enabled by default**. All command responses are returned as structured JSON for easy parsing. Use `--json false` to switch to human-readable text output.

### Global Options

```bash
remote-agent-browser [OPTIONS] <COMMAND> [ARGS...]

--gateway <url>       Gateway URL (env: REMOTE_AGENT_BROWSER_GATEWAY, default: http://localhost:8090)
--token <jwt>         JWT token (env: REMOTE_AGENT_BROWSER_TOKEN)
--browser <name>      Browser selection (env: REMOTE_AGENT_BROWSER_BROWSER)
--base-url <url>      Platform API base URL (env: REMOTE_AGENT_BROWSER_BASE_URL, default: https://mulerun.com)
--json [true|false]   JSON output (default: true)
--timeout <ms>        Command timeout in milliseconds (default: 30000)
```

## Authorization Flow

When connecting to a remote browser session, the browser extension on the user's machine must authorize access.

### Step 1: Attempt to connect

```bash
remote-agent-browser --token <jwt> open https://example.com
```

If not yet authorized, the CLI exits with `authorization_pending`. **Tell the user** you are requesting browser access, then call `wait-auth`:

```bash
remote-agent-browser --token <jwt> wait-auth
```

An authorization card will appear in the chat UI with "Authorize" and "No, use default browser" buttons. Tell the user to click "Authorize" in the card that appeared.

`wait-auth` internally polls until the user approves or rejects (default timeout: 120s). It returns when:
- **Authorized** — `{ "authorized": true }`, exit code 0
- **Rejected** — `{ "authorized": false, "reason": "authorization_rejected" }`, exit code 1
- **Timeout** — `{ "authorized": false, "reason": "timeout" }`, exit code 1

### Step 2: Handle the result

- **Authorized** — retry the original command.
- **Rejected** — the rejection is cached server-side and **cannot be retried in the same session**. **Immediately switch to the Playwright CLI** to open a cloud browser and complete the user's task. Do not ask the user — just proceed with the Playwright CLI. **For all subsequent browser tasks in this session, use the Playwright CLI directly — do not attempt `open` or `wait-auth` again.** Only if the user explicitly insists on using their local remote browser, tell them the rejection is cached and they need to start a new task to re-authorize.
- **Timeout** — the user has not responded yet. Call askuserquestion with **exactly** these two options every time — do not rephrase or reword them:
  - Option 1: **My Browser** — description: "Continue using My Browser"
  - Option 2: **Cloud browser** — description: "Switch to a cloud browser"

  If the user chooses "My Browser", call `wait-auth` again. If it times out again, call askuserquestion again with the **same two options above**. Repeat this cycle indefinitely — never treat a timeout as a final failure. If the user chooses "Cloud browser", switch to the Playwright CLI.

### Complete Workflow

```bash
# 1. Try to connect — get authorization_pending error
remote-agent-browser --token $JWT open https://example.com

# 2. Tell user you are requesting access, then wait for authorization
remote-agent-browser --token $JWT wait-auth

# 3a. Authorized → retry the original command
remote-agent-browser --token $JWT open https://example.com

# 3b. Rejected → switch to Playwright CLI immediately

# 3c. Timeout → askuserquestion: "My Browser" or "cloud browser"
#     User chooses My Browser → call wait-auth again → if timeout, repeat this cycle
#     User chooses cloud browser → switch to Playwright CLI
```

### Closing a Session

**Do NOT close the session after completing a task.** Only close when the user explicitly says they are done with the browser or asks to close.

```bash
remote-agent-browser --token $JWT close
```

## Core Workflow

Every browser automation follows this pattern:

1. **Navigate**: `remote-agent-browser open <url>`
2. **Snapshot**: `remote-agent-browser snapshot -i` (get element refs like `@e1`, `@e2`)
3. **Interact**: Use refs to click, fill, select
4. **Re-snapshot**: After navigation or DOM changes, get fresh refs

```bash
remote-agent-browser --token $JWT open https://example.com/form
remote-agent-browser snapshot -i
# Output: @e1 [input type="email"], @e2 [input type="password"], @e3 [button] "Submit"

remote-agent-browser fill @e1 "user@example.com"
remote-agent-browser fill @e2 "password123"
remote-agent-browser click @e3
remote-agent-browser wait --load domcontentloaded
remote-agent-browser snapshot -i  # Check result
```

## Command Chaining

Commands can be chained with `&&` in a single shell invocation. The browser session persists between commands via the daemon, so chaining is safe and more efficient than separate calls.

```bash
# Chain open + wait + snapshot in one call
remote-agent-browser open https://example.com && remote-agent-browser wait --load domcontentloaded && remote-agent-browser snapshot -i

# Chain multiple interactions
remote-agent-browser fill @e1 "user@example.com" && remote-agent-browser fill @e2 "password123" && remote-agent-browser click @e3
```

**When to chain:** Use `&&` when you don't need to read the output of an intermediate command before proceeding. Run commands separately when you need to parse the output first (e.g., snapshot to discover refs, then interact using those refs).

## Essential Commands

```bash
# Navigation
remote-agent-browser open <url>              # Navigate (aliases: goto, navigate)
remote-agent-browser close                   # Close browser

# Snapshot
remote-agent-browser snapshot -i             # Interactive elements with refs (recommended)
remote-agent-browser snapshot -i -C          # Include cursor-interactive elements
remote-agent-browser snapshot -s "#selector" # Scope to CSS selector

# Interaction (use @refs from snapshot)
remote-agent-browser click @e1               # Click element
remote-agent-browser click @e1 --new-tab     # Click and open in new tab
remote-agent-browser fill @e2 "text"         # Clear and type text
remote-agent-browser type @e2 "text"         # Type without clearing
remote-agent-browser select @e1 "option"     # Select dropdown option
remote-agent-browser check @e1               # Check checkbox
remote-agent-browser press Enter             # Press key
remote-agent-browser keyboard type "text"    # Type at current focus (no selector)
remote-agent-browser scroll down 500         # Scroll page
remote-agent-browser scroll down 500 --selector "div.content"  # Scroll within container

# Get information
remote-agent-browser get text @e1            # Get element text
remote-agent-browser get url                 # Get current URL
remote-agent-browser get title               # Get page title

# Wait (prefer domcontentloaded or load — avoid networkidle, it hangs on long-polling/SSE pages)
remote-agent-browser wait @e1                # Wait for element
remote-agent-browser wait --load domcontentloaded # Wait for DOM content loaded (recommended)
remote-agent-browser wait --load load              # Wait for full page load
remote-agent-browser wait --url "**/page"    # Wait for URL pattern
remote-agent-browser wait 2000               # Wait milliseconds
remote-agent-browser wait --text "Welcome"   # Wait for text to appear
remote-agent-browser wait --fn "!document.body.innerText.includes('Loading...')"  # Wait for text to disappear
remote-agent-browser wait "#spinner" --state hidden  # Wait for element to disappear

# Downloads
remote-agent-browser download @e1 ./file.pdf          # Click element to trigger download
remote-agent-browser wait --download ./output.zip     # Wait for any download to complete

# Network
remote-agent-browser network requests                 # Inspect tracked requests
remote-agent-browser network route "**/api/*" --abort  # Block matching requests

# Viewport & Device Emulation
remote-agent-browser set viewport 1920 1080          # Set viewport size (default: 1280x720)
remote-agent-browser set viewport 1920 1080 2        # 2x retina
remote-agent-browser set device "iPhone 14"          # Emulate device

# Capture
remote-agent-browser screenshot              # Screenshot to temp dir
remote-agent-browser screenshot --full       # Full page screenshot
remote-agent-browser screenshot --annotate   # Annotated screenshot with numbered element labels
remote-agent-browser pdf output.pdf          # Save as PDF

# Clipboard
remote-agent-browser clipboard read          # Read text from clipboard
remote-agent-browser clipboard write "text"  # Write text to clipboard

# Diff (compare page states)
remote-agent-browser diff snapshot           # Compare current vs last snapshot
remote-agent-browser diff screenshot --baseline before.png  # Visual pixel diff
```

## Batch Execution

Execute multiple commands in a single invocation by piping a JSON array:

```bash
echo '[
  ["open", "https://example.com"],
  ["snapshot", "-i"],
  ["click", "@e1"],
  ["screenshot", "result.png"]
]' | remote-agent-browser batch --json

# Stop on first error
remote-agent-browser batch --bail < commands.json
```

## Common Patterns

### Form Submission

```bash
remote-agent-browser open https://example.com/signup
remote-agent-browser snapshot -i
remote-agent-browser fill @e1 "Jane Doe"
remote-agent-browser fill @e2 "jane@example.com"
remote-agent-browser select @e3 "California"
remote-agent-browser check @e4
remote-agent-browser click @e5
remote-agent-browser wait --load domcontentloaded
```

### Working with Iframes

Iframe content is automatically inlined in snapshots. Refs inside iframes carry frame context, so you can interact with them directly.

```bash
remote-agent-browser open https://example.com/checkout
remote-agent-browser snapshot -i
# @e1 [heading] "Checkout"
# @e2 [Iframe] "payment-frame"
#   @e3 [input] "Card number"

remote-agent-browser fill @e3 "4111111111111111"
remote-agent-browser click @e5

# Scope to one iframe:
remote-agent-browser frame @e2
remote-agent-browser snapshot -i
remote-agent-browser frame main          # Return to main frame
```

### Data Extraction

```bash
remote-agent-browser open https://example.com/products
remote-agent-browser snapshot -i
remote-agent-browser get text @e5           # Get specific element text
remote-agent-browser get text body > page.txt  # Get all page text

# JSON output for parsing
remote-agent-browser snapshot -i --json
remote-agent-browser get text @e1 --json
```

### Parallel Sessions

Sessions are isolated by the platform. Use `session list` to see active sessions.

```bash
remote-agent-browser session list
```

### Viewport & Responsive Testing

```bash
remote-agent-browser set viewport 1920 1080
remote-agent-browser screenshot desktop.png

remote-agent-browser set viewport 375 812
remote-agent-browser screenshot mobile.png

remote-agent-browser set device "iPhone 14"
remote-agent-browser screenshot device.png
```

### JavaScript Evaluation

```bash
# Simple expressions
remote-agent-browser eval 'document.title'

# Complex JS: use --stdin with heredoc (RECOMMENDED)
remote-agent-browser eval --stdin <<'EVALEOF'
JSON.stringify(
  Array.from(document.querySelectorAll("img"))
    .filter(i => !i.alt)
    .map(i => ({ src: i.src.split("/").pop(), width: i.width }))
)
EVALEOF

# Base64 encoding (avoids all shell escaping issues)
remote-agent-browser eval -b "$(echo -n 'Array.from(document.querySelectorAll("a")).map(a => a.href)' | base64)"
```

## Security

### Content Boundaries (Recommended for AI Agents)

```bash
export REMOTE_AGENT_BROWSER_CONTENT_BOUNDARIES=1
remote-agent-browser snapshot
# Output wrapped in markers to help LLMs distinguish tool output from page content
```

### Domain Allowlist

```bash
export REMOTE_AGENT_BROWSER_ALLOWED_DOMAINS="example.com,*.example.com"
remote-agent-browser open https://example.com        # OK
remote-agent-browser open https://malicious.com       # Blocked
```

### Action Policy

```bash
export REMOTE_AGENT_BROWSER_ACTION_POLICY=./policy.json
```

## Session Management and Cleanup

**Do NOT proactively close the session.** Only close when the user explicitly asks to.

```bash
remote-agent-browser close
```

Auto-shutdown after inactivity:

```bash
REMOTE_AGENT_BROWSER_IDLE_TIMEOUT_MS=60000 remote-agent-browser open example.com
```

## Ref Lifecycle (Important)

Refs (`@e1`, `@e2`, etc.) are invalidated when the page changes. Always re-snapshot after:

- Clicking links or buttons that navigate
- Form submissions
- Dynamic content loading (dropdowns, modals)

```bash
remote-agent-browser click @e5              # Navigates to new page
remote-agent-browser snapshot -i            # MUST re-snapshot
remote-agent-browser click @e1              # Use new refs
```

## Annotated Screenshots (Vision Mode)

```bash
remote-agent-browser screenshot --annotate
# Output includes image path and legend:
#   [1] @e1 button "Submit"
#   [2] @e2 link "Home"
remote-agent-browser click @e2              # Click using ref from annotated screenshot
```

## Semantic Locators (Alternative to Refs)

```bash
remote-agent-browser find text "Sign In" click
remote-agent-browser find label "Email" fill "user@test.com"
remote-agent-browser find role button click --name "Submit"
remote-agent-browser find placeholder "Search" type "query"
remote-agent-browser find testid "submit-btn" click
```

## Deep-Dive Documentation

| Reference                                                            | When to Use                                               |
| -------------------------------------------------------------------- | --------------------------------------------------------- |
| [references/commands.md](references/commands.md)                     | Full command reference with all options                   |
| [references/snapshot-refs.md](references/snapshot-refs.md)           | Ref lifecycle, invalidation rules, troubleshooting        |
| [references/session-management.md](references/session-management.md) | Parallel sessions, state persistence, concurrent scraping |
| [references/authentication.md](references/authentication.md)         | Login flows, OAuth, 2FA handling, state reuse             |
| [references/video-recording.md](references/video-recording.md)       | Recording workflows for debugging and documentation       |
| [references/profiling.md](references/profiling.md)                   | Chrome DevTools profiling for performance analysis        |
| [references/proxy-support.md](references/proxy-support.md)           | Proxy configuration, geo-testing, rotating proxies        |

## Ready-to-Use Templates

| Template                                                                 | Description                         |
| ------------------------------------------------------------------------ | ----------------------------------- |
| [templates/form-automation.sh](templates/form-automation.sh)             | Form filling with validation        |
| [templates/authenticated-session.sh](templates/authenticated-session.sh) | Login once, reuse state             |
| [templates/capture-workflow.sh](templates/capture-workflow.sh)           | Content extraction with screenshots |
