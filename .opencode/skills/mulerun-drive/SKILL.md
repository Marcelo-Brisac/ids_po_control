---
name: mulerun-drive
description: "MuleRun Drive: Search, download, upload and manage cloud files. Trigger when user needs to find, retrieve, or manage files from MuleRun cloud storage."
---

# MuleRun Drive

> **For global flags, see `../mulerun-shared/SKILL.md`**
> **CRITICAL:** Never expose `mulerun` commands, CLI flags, or raw output to the user. See shared SKILL.md for full rules.

MuleRun Drive is a cloud file storage system. Files here persist across sessions.
This is MuleRun's own storage — NOT Google Drive or local filesystem.

## Key Commands

### search — Search files in Drive
Find files by name keyword. Essential for locating previous session outputs.

```bash
mulerun drive search <query> [--limit N]
```

**Example:**
```bash
mulerun drive search "报告"          # Search files containing "报告"
mulerun drive search "logo.png"      # Exact search
```

### download — Download file to local
Download a file from Drive to the local sandbox filesystem.

```bash
mulerun drive download <remote-path> [local-path]
mulerun drive download <remote-path> --dest <local-path>
```

- `remote-path` — File path in MuleRun Drive (must be a file, not directory)
- `local-path` or `--dest` — Local output path (default: CWD + remote filename)

**Examples:**
```bash
mulerun drive download /reports/q4.pdf              # → ./q4.pdf
mulerun drive download /assets/logo.png /tmp/       # → /tmp/logo.png
mulerun drive download /data.csv --dest result.csv  # → ./result.csv
```

### Common Scenarios

**Using outputs from a previous session:**
1. `mulerun drive search "报告"` → find matching files
2. `mulerun drive download <path>` → download to local
3. Process the file locally

**Using existing assets for new tasks:**
1. `mulerun drive search "logo"` → find the asset
2. `mulerun drive download <path>` → download
3. Use the asset in current task

## Other Commands
For additional drive operations, run `mulerun drive --help`:
- `ls` — List directory contents
- `mkdir` — Create a directory
- `stat` — Get file details (size, type, timestamps)
- `upload` — Upload a local file to Drive
- `cp` — Copy a file within Drive
- `share` — Create/manage share links (create, list, get, access)
- `public` — Manage public file access (set, get, list)
