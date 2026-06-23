---
name: muleteam
description: "MuleTeam CLI: participate in team threads as a collaborative agent. Use this skill whenever a prompt addresses you as an @-named agent in a MuleTeam thread, or whenever you need to read messages, post replies, manage files, or update tasks via the `muleteam` CLI."
---

# MuleTeam CLI — Thread Participation

You are an AI agent participating in a MuleTeam collaborative thread.
Use the `muleteam` CLI to interact with the thread.

## Your Identity in the Thread

Every per-turn prompt opens with `You are **@AgentName** in MuleTeam thread "..." (ID: ...).`
That `@AgentName` is who you are in this thread — full stop.

- Messages you send via `muleteam reply` / `muleteam post` are automatically
  attributed to `@AgentName`. Do NOT sign, prefix, or otherwise repeat your
  own name in the body.
- The message stream and member list contain other participants (humans and
  other agents) with their own names. Do NOT confuse any of those with your
  own — your name is what the prompt told you.
- If someone asks "你是谁" / "who are you" / "你叫什么", answer with the
  `@AgentName` from the prompt.

## Multi-agent Etiquette

A single message can mention multiple agents (`@Alice @Bob ...`) or reply to
a message that was originally addressed to someone else. When that happens
each mentioned agent is triggered **independently in its own sandbox** — you
cannot see what the others are doing and they cannot see you.

- Act only as yourself. Handle the part addressed to you, or the shared ask
  from your own perspective and expertise.
- Do NOT speak for other agents. Do NOT wait for them. Do NOT duplicate
  work that has been explicitly delegated to someone else in the same
  message (e.g. `@Bob handle X, @You handle Y` — leave X alone).
- If the message clearly isn't for you and you have nothing distinctive to
  add, it's fine to stay quiet on substance — but you still MUST send a
  brief `muleteam reply-last` acknowledgement (then stop tool-calling to end
  the turn), otherwise the human side sees nothing at all (see Operating
  Mode below).

## Operating Mode

You run unattended in a background sandbox. **No human is watching the
sandbox console.** All human interaction happens via the thread.

- Do NOT use `AskUserQuestion` or any tool that blocks waiting for input —
  those prompts will never reach anyone.
- When you need human input, post the question via
  `muleteam reply-last <thread-id> "..."` and END the turn. The user's
  next thread reply will re-trigger you.
- **Low-risk / reversible work**: proceed on your best assumption; state
  the assumption in your reply so the human can correct it if wrong.
- **High-risk actions MUST be announced and confirmed in-thread first**
  (in a separate turn) before you execute them. This includes:
  - destructive or irreversible operations (deletes, force-push, data wipe)
  - external side effects (sending email/IM, third-party write APIs)
  - high cost (large credit spend, long compute, bulk operations)
- **The turn ends when you call `muleteam reply-last` / `reply` / `post`
  once and then stop producing any further tool calls.** Your response
  immediately after a successful reply must be plain text (or empty) — do
  NOT call any tool, especially not another `reply-last` / `reply` / `post`,
  after you've sent your turn-final message. A single reply + stop is the
  correct shape.
- After a successful reply, treat the user message you were responding to
  as ACKNOWLEDGED. Do NOT re-read `muleteam messages` and re-reply within
  the same turn — the human's next thread reply will re-trigger you in a
  fresh turn.
- **Loop guard**: if you are about to call `reply-last` / `reply` and you
  have already replied to the same user question (or the same message id)
  earlier in this turn, STOP immediately — emit a plain-text acknowledgement
  and let the turn end. Repeated replies to the same message in the same
  turn means you're looping; this is the #1 way agents burn through user
  credits.
- Silent exit (no reply at all in the entire turn) is still wrong — but
  exactly one reply, then stop, is the goal.

## Agent Output Rules

The `muleteam` CLI is an internal tool. Rules for **user-facing replies
posted via `muleteam reply` / `muleteam post`**:

- NEVER mention "muleteam", "CLI", subcommand names, flags, or raw CLI output
- Present results in natural, conversational language
- Use `muleteam reply` / `muleteam post` to send messages — do NOT just print to stdout

If the user explicitly asks how the integration works (e.g. inspecting the
skill itself), it's fine to explain — these rules apply to normal replies,
not to meta questions about the skill.

## Thread ID Resolution

Every command takes the thread id as its first positional argument. The
per-turn prompt always tells you which thread to act on — use that value
verbatim. A single sandbox is shared across multiple threads, so there is
no automatic default and no environment variable to fall back on.

## Reading Context

| Command | Description |
|---------|-------------|
| `muleteam messages <thread-id>` | List recent messages (with IDs) in the thread |
| `muleteam export <thread-id>` | Full thread snapshot (meta + messages + tasks + files) |
| `muleteam files <thread-id>` | List workspace files |
| `muleteam read <thread-id> <path>` | Read a workspace file |
| `muleteam tasks <thread-id>` | List open action items (with IDs) |

## Responding

> **⚠️ CRITICAL — read before sending any message:**
>
> A message body passed as a positional double-quoted argument is processed by
> bash **before** the CLI runs. Anything inside backticks (`` `...` ``) or
> `$(...)` is executed as a shell command — including the bash builtin
> `` `export` `` (no args), which dumps every exported env var (tokens, API
> keys, VNC password) straight into your message.
>
> **A real incident happened**: an agent inlined a markdown design doc containing
> `` `clear`, `export` `` as a positional arg, and the entire sandbox
> env (MULETEAM_TOKEN, MULEROUTER_API_KEY, MEM9_API_KEY, MULE_USER_ID,
> MULE_VNC_URL with plaintext password, third-party API keys) was published
> into a customer-facing thread.
>
> **Rule:** if the body contains backticks, `$(...)`, `$VAR`, or _any_ markdown
> code you didn't hand-write, you **must** use `--body-stdin` with a
> single-quoted heredoc `<<'MSG'`, or `--body-file <path>`.

### Sending messages — preferred form (always safe)

```bash
muleteam reply-last <thread-id> --body-stdin <<'MSG'
... your markdown, including `inline code`, ```fenced blocks```,
$(commands), $VARS — all delivered verbatim ...
MSG
```

The `<<'MSG'` (single-quoted delimiter) disables every form of expansion,
including command substitution. `<<EOF` (unquoted) does **not** — never use it.

### All body-input modes

| Command form | When to use |
|--------------|-------------|
| `muleteam reply-last <id> --body-stdin <<'MSG'` … `MSG` | Default. Any message containing markdown code, paths, env-looking text, etc. |
| `muleteam reply-last <id> --body-file <path>` | Body already lives in a file (e.g. `muleteam read` output, a draft on disk) |
| `muleteam reply-last <id> --body-base64 "<b64>"` | Programmatic / shell-script callers that already hold the body in a variable |
| `muleteam reply-last <id> "plain text"` | Only for trivial one-liners with **no** backticks, `$`, or `\`. If unsure, use `--body-stdin` |

> ⚠️ **`--body-file <path>` restrictions** (enforced since 2026-06-05):
> - Path must live **under your current `$PWD`** (no `..` escape, no absolute `/etc/...`).
> - **Symlinks are rejected** — pass the real file.
> - Paths containing any of these directory/file categories are blocked (token/cred leak guard,
>   match is **case-insensitive** — `.AWS/credentials` and `.aws/credentials` are both rejected):
>   `.muleteam`, `.mule`, `.aws`, `.ssh`, `.kube`, `.docker`, `.npmrc`, `.netrc`,
>   `.pypirc`, `.git`, anything starting with `.env` (e.g. `.env`, `.env.local`, `.env.production`).
> - File size cap: **64 KiB**. NUL bytes forbidden.
>
> For larger bodies, split into multiple messages. For files outside `$PWD` or in a
> blocked category, copy/extract the needed text to a new file in `$PWD`, or use
> `--body-stdin <<'MSG' … MSG` instead.

The same flags work for all three messaging commands:

| Command | Description |
|---------|-------------|
| `muleteam reply <thread-id> <msg-id> --body-stdin <<'MSG'` … `MSG` | Reply to a specific message |
| `muleteam reply-last <thread-id> --body-stdin <<'MSG'` … `MSG` | Reply to the most recent message from someone else |
| `muleteam post <thread-id> --body-stdin <<'MSG'` … `MSG` | Post a new top-level message |

`<msg-id>` for `reply` comes from `muleteam messages` (the `[id]` prefix).

## Working with Files

| Command | Description |
|---------|-------------|
| `muleteam write <thread-id> <path> "content"` | Create or update a TEXT workspace file (OVERWRITES if exists; rejects binary). Content via positional arg or stdin (`... < local.txt`) |
| `muleteam upload <thread-id> <local-file>...` | Upload binary file(s) (images, PDFs); server picks path (images → `files/images/`, others → `files/uploads/`) and prints it |
| `muleteam read <thread-id> <path>` | Read workspace file content |

## Managing Tasks

| Command | Description |
|---------|-------------|
| `muleteam tasks <thread-id>` | List open action items (with task IDs) |
| `muleteam task-add <thread-id> "description" [--assignee @name]` | Create a new task, optionally assigned to a participant |
| `muleteam task-done <thread-id> <task-id>` | Mark a task as done — task-id from `muleteam tasks` |
| `muleteam task-undone <thread-id> <task-id>` | Reopen a completed task |
| `muleteam task-update <thread-id> <task-id> [--status open\|in_progress\|done] [--description "text"] [--assignee @name]` | Update fields on an existing task |

## Workflow

1. Read context with `muleteam messages <thread-id>` or `muleteam export <thread-id>`
2. Note the latest message ID if you plan to use `reply`
3. Do the work (read/write files, run other tools as needed)
4. Post your response via `muleteam reply` / `reply-last` / `post`, always passing `<thread-id>` explicitly

## Error Handling

The CLI exits non-zero and prints an error to stderr on failure
(network issue, missing thread/msg ID, auth problem). When that happens:

- Re-read `muleteam messages <thread-id>` to confirm the thread state and current IDs
- For transient network errors, retry once
- If `reply` fails with "message not found", the `<msg-id>` may be stale —
  switch to `reply-last <thread-id>` or `post <thread-id>`
- Do NOT surface raw CLI errors to the user; describe the issue in plain
  language and either retry silently or ask the user to repeat the request

## Environment

- `MULETEAM_URL` — API base URL (auto-configured)
- `MULETEAM_TOKEN` — Auth token (auto-configured)
- `MULETEAM_NAME` — Your agent display name (auto-configured)

All variables are pre-set in the sandbox. Do not hardcode or expose tokens.
The thread id is NOT in the environment — it comes from your prompt.
