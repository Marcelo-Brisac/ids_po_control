---
name: mulerun-session
description: "MuleRun Session: introspect existing sessions or run sub-agents in parallel. Sub-agent commands (create / run / prompt / chat / cancel / publish / question) only work when multi-agent mode is on for this chat; without it, only read-only inspection (list / get / events) works."
---

# MuleRun Session

> **For global flags, see `../mulerun-shared/SKILL.md`**
> **CRITICAL:** Never expose `mulerun` commands, CLI flags, or raw output to the user. See shared SKILL.md for full rules.

## Read-only — always works

```bash
mulerun session list                  # list this user's sessions
mulerun session get <session-id>      # session detail
mulerun session events <session-id>   # session event log
```

## Sub-agent commands — only when multi-agent mode is on

```bash
mulerun session run --name "researcher" --prompt "..." --wait=false
mulerun session create --name "..." --wait=false
mulerun session chat <session-id> --prompt "..."
mulerun session cancel <session-id>
mulerun session publish <session-id>
mulerun session question <session-id> <tool-call-id> <outcome>
```

If any of these returns `multi-agent mode is not enabled for this chat`,
the user did **not** turn on multi-agent. **Do not retry. Do not surface
the error verbatim. Do not suggest workarounds, settings, or commands.**
Just continue the task inside the current chat with whatever tools you
already have. If a multi-agent plan is the only way to answer well, ask
the user to enable Multi-Agent mode and stop.
