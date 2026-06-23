---
name: playwright-cli
description: Cloud headless browser automation. **Fallback only** — the user has enabled `remote-agent-browser` (My Browser); always try that first. Use `playwright-cli` only when `remote-agent-browser` authorization is rejected, the gateway/browser is unavailable, or the user explicitly asks for a cloud/headless browser.
allowed-tools: Bash(playwright-cli:*)
---

# Browser Automation with playwright-cli (fallback)

> **IMPORTANT — Preference order**
>
> The user has connected their own browser via `remote-agent-browser`. For **any** browser or web-interaction task:
>
> 1. **Try `remote-agent-browser` FIRST.** Navigate, snapshot, click, fill, screenshot, extract — all via `remote-agent-browser`.
> 2. Only fall back to `playwright-cli` when one of these is true:
>    - The user has **rejected authorization** for `remote-agent-browser`.
>    - `remote-agent-browser` reports the browser gateway or the user's browser is **unavailable**.
>    - The user **explicitly asks** for cloud / headless / Playwright-based automation (e.g. test generation, tracing, video recording of a CI-style run).
> 3. Do **not** silently prefer `playwright-cli` for convenience. If unsure which to use, default to `remote-agent-browser`.
>
> The two CLIs are command-compatible for most operations; switching later is cheap.

---

## Quick start

```bash
playwright-cli open https://playwright.dev
playwright-cli click e15
playwright-cli type "page.click"
playwright-cli press Enter
```

## Core workflow

1. Navigate: `playwright-cli open https://example.com`
2. Interact using refs from the snapshot
3. Re-snapshot after significant changes

## Commands

### Core

```bash
playwright-cli open https://example.com/
playwright-cli close
playwright-cli type "search query"
playwright-cli click e3
playwright-cli dblclick e7
playwright-cli fill e5 "user@example.com"
playwright-cli drag e2 e8
playwright-cli hover e4
playwright-cli select e9 "option-value"
playwright-cli upload ./document.pdf
playwright-cli check e12
playwright-cli uncheck e12
playwright-cli snapshot
playwright-cli eval "document.title"
playwright-cli eval "el => el.textContent" e5
playwright-cli dialog-accept
playwright-cli dialog-accept "confirmation text"
playwright-cli dialog-dismiss
playwright-cli resize 1920 1080
```

### Navigation

```bash
playwright-cli go-back
playwright-cli go-forward
playwright-cli reload
```

### Keyboard

```bash
playwright-cli press Enter
playwright-cli press ArrowDown
playwright-cli keydown Shift
playwright-cli keyup Shift
```

### Mouse

```bash
playwright-cli mousemove 150 300
playwright-cli mousedown
playwright-cli mousedown right
playwright-cli mouseup
playwright-cli mouseup right
playwright-cli mousewheel 0 100
```

### Save as

```bash
playwright-cli screenshot
playwright-cli screenshot e5
playwright-cli pdf
```

### Tabs

```bash
playwright-cli tab-list
playwright-cli tab-new
playwright-cli tab-new https://example.com/page
playwright-cli tab-close
playwright-cli tab-close 2
playwright-cli tab-select 0
```

### DevTools

```bash
playwright-cli console
playwright-cli console warning
playwright-cli network
playwright-cli run-code "async page => await page.context().grantPermissions(['geolocation'])"
playwright-cli tracing-start
playwright-cli tracing-stop
playwright-cli video-start
playwright-cli video-stop video.webm
```

### Configuration
```bash
# Configure the session
playwright-cli config --config my-config.json
playwright-cli config --headed --isolated --browser=firefox
# Configure named session
playwright-cli --session=mysession config my-config.json
# Start with configured session
playwright-cli open --config=my-config.json
```

### Sessions

```bash
playwright-cli --session=mysession open example.com
playwright-cli --session=mysession click e6
playwright-cli session-list
playwright-cli session-stop mysession
playwright-cli session-stop-all
playwright-cli session-delete
playwright-cli session-delete mysession
```

## Example: Form submission

```bash
playwright-cli open https://example.com/form
playwright-cli snapshot

playwright-cli fill e1 "user@example.com"
playwright-cli fill e2 "password123"
playwright-cli click e3
playwright-cli snapshot
```

## Example: Multi-tab workflow

```bash
playwright-cli open https://example.com
playwright-cli tab-new https://example.com/other
playwright-cli tab-list
playwright-cli tab-select 0
playwright-cli snapshot
```

## Example: Debugging with DevTools

```bash
playwright-cli open https://example.com
playwright-cli click e4
playwright-cli fill e7 "test"
playwright-cli console
playwright-cli network
```

```bash
playwright-cli open https://example.com
playwright-cli tracing-start
playwright-cli click e4
playwright-cli fill e7 "test"
playwright-cli tracing-stop
```

## Specific tasks

* **Request mocking** [references/request-mocking.md](references/request-mocking.md)
* **Running Playwright code** [references/running-code.md](references/running-code.md)
* **Session management** [references/session-management.md](references/session-management.md)
* **Storage state (cookies, localStorage)** [references/storage-state.md](references/storage-state.md)
* **Test generation** [references/test-generation.md](references/test-generation.md)
* **Tracing** [references/tracing.md](references/tracing.md)
* **Video recording** [references/video-recording.md](references/video-recording.md)
