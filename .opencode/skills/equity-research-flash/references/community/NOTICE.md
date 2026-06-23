# NOTICE

The eleven `.md` files alongside this file are community-contributed
analyst lenses vendored from the [`prof-little-bear/cc-equity-research`](https://github.com/prof-little-bear/cc-equity-research)
repository.

**Upstream:** https://github.com/prof-little-bear/cc-equity-research
**Source path:** `community-skills/`
**Vendored at commit:** `7c428944a6718c35461f839c618ae66334b6371b`
**Vendored on:** 2026-06-03
**License:** Apache License 2.0 (see upstream `LICENSE`)

---

## What's vendored

Eleven of the fifteen upstream community skills:

| File | Upstream subpath |
|---|---|
| `themes.md` | `discover/themes.md` |
| `business-model.md` | `analyze/business-model.md` |
| `earnings-scorecard.md` | `analyze/earnings-scorecard.md` |
| `financial-forensics.md` | `analyze/financial-forensics.md` |
| `reporting-quality.md` | `analyze/reporting-quality.md` |
| `management.md` | `analyze/management.md` |
| `watchlist.md` | `monitor/watchlist.md` |
| `thesis-check.md` | `monitor/thesis-check.md` |
| `event-radar.md` | `monitor/event-radar.md` |
| `yield-curve.md` | `economic-research/yield-curve.md` |
| `labor-market.md` | `economic-research/labor-market.md` |

## Skipped (data-source gap)

Four upstream skills are NOT vendored. They lean on alternative-data
sources (federal contracts, supply-chain ontology, customs flows,
peer-group lookups) that this skill bundle does not yet wire up:

- `discover/alt-plays.md` — needs peer-ontology lookups
- `discover/supply-chain.md` — needs supplier/customer ontology
- `discover/gov-contracts.md` — needs federal-contract feed
- `economic-research/trade-flows.md` — needs HS-code customs feed

Revisit when those data sources are wired into the workspace skills.

## Modifications

**None.** Files are reproduced verbatim from upstream. The upstream
references to a `drillr` MCP and to `mcp__drillr__*` tools are left
as-is in the doc text; the parent dispatcher (`equity-research/SKILL.md`)
overrides the data-routing rule to point to this workspace's
`global-markets` / `cn-markets` / `macro-rates-fx` / `crypto-markets`
skills via `references/routing.md`. When this skill's dispatcher
disagrees with a referenced methodology doc on which tool to call, the
dispatcher wins.

If any file is later modified directly, mark the modification at the
top of that file per Apache 2.0 §4(b).

## Updating

```bash
git clone --depth 1 https://github.com/prof-little-bear/cc-equity-research.git /tmp/cc-eq
diff -r /tmp/cc-eq/community-skills/ \
    packages/mule-skill-equity-research/opt/agent-skills/equity-research/references/community/ | head -50
# Review and merge changes manually; update commit SHA + date above.
```
