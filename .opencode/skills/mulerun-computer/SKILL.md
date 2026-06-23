---
name: mulerun-computer
description: "MuleRun Computer: Manage, repair, and interact with compute instances. Trigger when user needs to check computer status, fix issues, chat with computer agent, access files on the instance, or create/manage scheduled tasks (定时任务/cron/interval/定期执行). Use 'mulerun computer schedule' for persistent scheduled tasks on the VM."
---

# MuleRun Computer

> **For global flags, see `../mulerun-shared/SKILL.md`**
> **Availability:** Requires an active plan. Run `mulerun computer list` to verify access — if you get a 403 error, computer features are not available for this user.
> **CRITICAL:** Never expose `mulerun` commands, CLI flags, or raw output to the user. See shared SKILL.md for full rules.

## Availability & Retry After Wake-up

Computer instances can be started/stopped by the user. If a previous command
failed with a connection error or "instance not running", **always re-check
before giving up**:

1. Run `mulerun computer list` to get the current instance status
2. If the instance is now running, **retry the original operation** — do NOT
   tell the user "computer is not available" based on a stale error
3. Only report unavailability after a fresh check confirms the instance is
   truly offline

**Never cache or remember a previous "unavailable" result across turns.**
The user may have just woken up the computer — always verify the live state.

MuleRun Computer provides managed compute instances for running persistent
workloads, SSH access, and AI-powered interactions.

## Repair & Health Check

When a compute instance is unresponsive or behaving abnormally, use these
commands to diagnose and fix:

### Diagnostic Flow
1. `mulerun computer list` → Check all instances and status
2. `mulerun computer state [id]` → Detailed state of target instance
3. `mulerun computer quickfix [id]` → Attempt quick repair
4. If quickfix fails → `mulerun computer reboot [id]` → Full restart

```bash
# Full repair workflow
mulerun computer list                    # Find instance
mulerun computer state                   # Check status (auto-detects instance)
mulerun computer quickfix                # Try quick fix first
mulerun computer reboot                  # Reboot if quickfix fails
```

## Chat with Computer

Communicate with the AI agent running on the compute instance:

```bash
mulerun computer chat --prompt "check recent errors in system logs"
mulerun computer send --prompt "check telegram messages" --session-id <id>
```

| Command | Description |
|---------|-------------|
| `chat` | Start new chat session (returns session-id + streaming response) |
| `send` | Continue existing chat (auto-detect or specify --session-id) |

**Flags:**
| Flag | Required | Description |
|------|----------|-------------|
| `--prompt` | Yes | Message to send |
| `-f` | No | Attach files |
| `--session-id` | No (send only) | Continue specific conversation |

## SSH & File System

```bash
mulerun computer ssh                     # SSH into instance
mulerun computer fs list /path           # List directory
mulerun computer fs read /path/file.txt  # Read file content
mulerun computer fs write /path/file.txt --from-file ./file.txt   # Upload local file (recommended, auto-chunks 512KB)
mulerun computer fs write /path/small.txt --content "..."         # Inline content (small strings only)
cat build.tar.gz | mulerun computer fs write /remote/build.tar.gz --from-stdin   # Pipe from stdin
```

**Troubleshooting**:
- `Argument list too long` when using `--content "$(cat bigfile)"` → switch to `--from-file <path>`. The shell's `ARG_MAX` (~256 KB on macOS/Linux) caps how much you can pass via argv.
- For any file > ~100 KB or binary data, always use `--from-file` or `--from-stdin`; they stream in 512 KB chunks and upload atomically (via `<path>.tmp` + rename).

For full SSH and file system operations, see `mulerun computer --help`:
- `ssh` — SSH into instance (keys auto-configured for paid users)
- `ssh-keygen`, `ssh-setup` — Key management (usually auto-handled)
- `fs list/stat/read/write/mkdir/rm/rename/cp/search` — File system operations

## Scheduled Tasks

For creating and managing scheduled tasks (recurring jobs, one-time future tasks),
see the dedicated skill: **`../mulerun-computer-schedule/SKILL.md`**
