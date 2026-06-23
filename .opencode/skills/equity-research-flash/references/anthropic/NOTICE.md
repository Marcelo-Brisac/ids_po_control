# NOTICE

The nine skill directories alongside this file are vendored from
Anthropic's open-source [`anthropics/financial-services`](https://github.com/anthropics/financial-services)
repository.

**Upstream:** https://github.com/anthropics/financial-services
**Source path:** `plugins/vertical-plugins/equity-research/skills/`
**Vendored at commit:** `120a31dcede4affa1d771cbf286a63ee331f92a4`
**Vendored on:** 2026-06-03
**License:** Apache License 2.0 (see `LICENSE` in this directory)

---

## What's vendored

Nine equity-research skills, copied verbatim from upstream:

- `catalyst-calendar`
- `earnings-analysis`
- `earnings-preview`
- `idea-generation`
- `initiating-coverage`
- `model-update`
- `morning-note`
- `sector-overview`
- `thesis-tracker`

## Modifications

The nine top-level `SKILL.md` files inside the subdirectories have
been renamed to `WORKFLOW.md`, per Apache 2.0 §4(b). Rationale:
opencode discovers skills via the recursive glob `**/SKILL.md`,
which would otherwise surface these nine workflow docs as peer
skills competing with the parent `equity-research`. Renaming keeps
them out of the discovery glob while leaving them readable on demand
by the parent dispatcher. File contents are otherwise unmodified. If
any file is later modified, the modification will be marked at the
top of that file per Apache 2.0 §4(b).

The renamed files inside each of the nine subdirectories are not
auto-discovered as skills by either Claude Code (one-level scan that
only ever looked at `<entry>/SKILL.md`) or opencode (recursive
`**/SKILL.md`, which no longer matches). The parent
`equity-research/SKILL.md` is the only discovered entry. The
`WORKFLOW.md` files are read on demand as methodology references by
the parent dispatcher.

## Trademark

This skill is not affiliated with or endorsed by Anthropic. The Anthropic
name and trademarks remain the property of Anthropic, PBC, and are
referenced here solely for descriptive attribution as permitted under
Apache 2.0 §6.

## Updating

To pull updates from upstream:

```bash
git clone --depth 1 https://github.com/anthropics/financial-services.git /tmp/financial-services
diff -r /tmp/financial-services/plugins/vertical-plugins/equity-research/skills/ \
    packages/mule-skill-equity-research/opt/agent-skills/equity-research/references/anthropic/ | head -50
# Review and merge changes manually; update commit SHA + date above.
```
