---
name: mulerun-computer-schedule
description: "Scheduled Tasks on Compute Instance: Create, manage, and monitor recurring or one-time scheduled tasks (定时任务/cron/interval/定期执行/每天/每小时/每分钟). Use 'mulerun computer schedule' to set up persistent automated jobs on the VM — backups, monitoring, weather checks, cleanup, etc."
---

# Scheduled Tasks on Compute Instance

> **For global flags, see `../mulerun-shared/SKILL.md`**
> **For other computer operations (repair, chat, SSH, file system), see `../mulerun-computer/SKILL.md`**
> **CRITICAL:** Never expose `mulerun` commands, CLI flags, or raw output to the user. See shared SKILL.md for full rules.
> **Availability:** Requires an active compute instance. If commands fail, run `mulerun computer list` to re-check — never assume "unavailable" from a stale error.

## Decision Guide

| User intent | Action |
|-------------|--------|
| Recurring ("every day / hour / minute") | `schedule create` |
| Time-limited recurring ("every minute for 5 min") | `schedule create`, then auto-delete after duration |
| Immediate one-off | `send` |
| Future one-off | `schedule create --schedule-type once` |

**Never write a bash script or loop to implement recurring tasks.**

## Commands

| Command | Purpose |
|---------|---------|
| `schedule list` | List all tasks with summary |
| `schedule create` | Create a new task |
| `schedule update <id>` | Update task fields |
| `schedule delete <id>` | Delete a task |
| `schedule logs <id>` | View execution history |

## Creating a Task

```bash
mulerun computer schedule create \
  --name "Task Name" \
  --prompt "instruction for the agent" \
  --schedule-type cron \
  --schedule-value "<cron expression>"
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--name` | yes | — | Human-readable name |
| `--prompt` | yes | — | Instruction for the agent to execute |
| `--schedule-type` | yes | — | `cron`, `interval`, or `once` |
| `--schedule-value` | yes | — | Value depends on type: standard 5-field cron expression / integer minutes for interval / ISO 8601 timestamp for once |
| `--description` | no | — | Task description |
| `--context-mode` | no | `isolated` | `isolated` or `group` |
| `--status` | no | `active` | `active` or `paused` |

## Workflow Examples

Internal execution vs. user-facing reply:

**Recurring task:**
```bash
mulerun computer schedule create --name "Nightly Backup" \
  --prompt "Run backup and verify integrity" \
  --schedule-type cron --schedule-value "<nightly cron expression>"
```
Reply: "All set! Your database will be backed up every night at 11pm."

**Time-limited task:**
```bash
mulerun computer schedule create --name "Weather Check" \
  --prompt "Search current Shanghai weather" \
  --schedule-type interval --schedule-value "<1-minute interval>"
```
Then use `schedule create --schedule-type once` to schedule deletion after 5 minutes.
Reply: "Done! I'll check Shanghai weather every minute and stop after 5 minutes."

**List / pause / resume:**
```bash
mulerun computer schedule list
mulerun computer schedule update <id> --status paused
```
Reply with a plain-language summary of task names, schedules, and status.
