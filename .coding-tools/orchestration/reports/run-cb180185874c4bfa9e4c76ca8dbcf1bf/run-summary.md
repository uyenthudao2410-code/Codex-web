# Orchestration Run Summary

- Run: `cb180185874c4bfa9e4c76ca8dbcf1bf`
- Task: `56e7faf786de413a865d1dfc2280293a`
- Objective: Repair the remaining extraction regressions found by the broad Python MCP suite without changing business behavior. Restore module-owned dependencies, P1 organic host-turn claim/binding helpers and orchestration integration, and Wave 2B public continuation scope forwarding. Preserve smart-v3 and existing server compatibility exports.
- Status: **accepted**
- Started: `2026-08-15T10:32:16.068Z`
- Finished: `2026-08-15T10:36:46.260Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `becbd66c5f3e4b3c9e9d9c2524ddaba8` | `mcp_only` | `7236cd6a72c27e6eb7679585c115220cc54ae842` | replanned |
| 2 | `7e5a638ac0be4277b541f18b391211a6` | `mcp_only` | `7236cd6a72c27e6eb7679585c115220cc54ae842` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 7e5f560677314b51b1699236141520cb | 7e5a638ac0be4277b541f18b391211a6 | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | fdb30a1430bb23ba34f50734ebd8984524640f47dfc7b5e1daad2278994b58ce | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 5256 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 5273 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 5268 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `32`
- Chain head: `8d09cbbbb5336be09c257b443966e17c8f2e1ee0618b883b97d36e01c1ec6224`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
