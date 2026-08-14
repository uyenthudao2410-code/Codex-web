# Orchestration Run Summary

- Run: `69d46ddf56f041e9bbf419ee53be295c`
- Task: `00bba534a5b744de850813dcf3d68076`
- Objective: P3B truthful idempotency gate observability. Keep cumulative PerformanceTrace v5 required coverage unchanged for audit, but introduce a named current auto-key policy epoch 'task_epoch_v1' with fresh required/keyed counters and bounded per-operation breakdown (calls,keyed,missing,missing_reasons). When loading a pre-epoch v5 file, preserve cumulative counters but initialize current-policy counters at zero; never backfill historical misses. Runtime emit_tool_trace must label required operations (agent_workflow:execute, task_control:accept/reject) and missing identity reason when a required key is absent. runtime_activation must report cumulative and current-policy coverage, use current-policy coverage as the decision gate only when the epoch exists, expose target 0.95/pass boolean, and retain legacy-v4 fallback. Add tests proving old 22/30 cumulative history stays intact while a new keyed current-policy sample yields 1.0 current coverage, plus per-operation accounting. No runtime reset/restart or history deletion.
- Status: **accepted**
- Started: `2026-08-14T18:13:22.354Z`
- Finished: `2026-08-14T18:15:05.489Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `e9ee856f73b24e1988065fb7cb76cc50` | `mcp_only` | `5decaa48300b10a6df39676c677745bc881cd7d9` | replanned |
| 2 | `62ff5963b81f4504af8abc2a8b4da640` | `mcp_only` | `5decaa48300b10a6df39676c677745bc881cd7d9` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 89c9435485794d3c817a61b1846e7be1 | 62ff5963b81f4504af8abc2a8b4da640 | accepted | 5decaa48300b10a6df39676c677745bc881cd7d9 | 1f73c264f82a5ca9808e6a44b4a0167661c71c65667353f2e2c863093ea2e1b6 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 3315 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 3325 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 3319 | `PATCH_CONTEXT_NOT_FOUND` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `b9aeec52ffd3c7db81e8a5c0124c6bae67463eff1779931d0d90eea281915c8b`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
