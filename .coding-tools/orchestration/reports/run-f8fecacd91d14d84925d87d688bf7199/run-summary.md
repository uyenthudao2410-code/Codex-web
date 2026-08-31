# Orchestration Run Summary

- Run: `f8fecacd91d14d84925d87d688bf7199`
- Task: `b01432fda48e408190519f7d9ac19e27`
- Objective: Apply only the exact-current Control Center slice of the truthful token-metering fix: render host Tool-call-card tokens as a separate evidence plane from MCP tools/list and controller/provider UsageEvents. Because the current MCP transport does not expose an exact post-call host receipt, render Tool-card tokens as unavailable rather than estimated. Preserve all unrelated bytes.
- Status: **aborted**
- Started: `2026-08-30T15:38:24.191Z`
- Finished: `2026-08-31T13:58:12.960Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `01947bc07f6f4eabbcef096499d3eeef` | 1 | `run_initial_objective` | `mcp_only` | `9b766f241432b9b5bfa8aa75ae2f1816709a2c2d` | replanned |
| 2 | `3b440b68b41a42db811477a98a1ec35a` | 2 | `replan_request` | `mcp_only` | `9b766f241432b9b5bfa8aa75ae2f1816709a2c2d` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 32751 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 32764 | `SOL_REJECTED` | `ACCEPTING` | Reject this partial wave as incomplete/unproven: it changed only Control Center and its source assertion, recorded zero proof, and does not yet implement the backend tool_call_metering projection or remove visible Dashboard byte-derived token fallback. Preserve the two applied files and replan the same RUN to complete the causal scope with focused Node/Python proof. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `25`
- Chain head: `20d5ee27aba2e18813565098be2b8f37d0ee32d0f4894d20aa5683a6f4691b12`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
