# Orchestration Run Summary

- Run: `7f39807c832e4750998a0280342f715e`
- Task: `1a6af0f65a7a435ca28816586369d387`
- Objective: Fix the full-suite regression introduced by auto-derived task_control accept/reject idempotency keys. Scope only accept/reject derived keys by current caller client_id and controller fencing_token so a denied stale client cannot poison a valid controller's key, and a new authority epoch gets a new key. Keep agent_workflow execute derivation unchanged, explicit keys unchanged, and idempotency failure semantics fail-closed. Add focused unit assertions.
- Status: **accepted**
- Started: `2026-08-14T16:33:20.965Z`
- Finished: `2026-08-14T16:37:27.458Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `2fac889ffaea47c8acfbd58e4fe04188` | `mcp_only` | `62ff046711503260b079e53a85c66e5b9af01e32` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| d58e02105993401fb176b18ccdb9cb3a | 2fac889ffaea47c8acfbd58e4fe04188 | accepted | 62ff046711503260b079e53a85c66e5b9af01e32 |  | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 2880 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `11`
- Chain head: `c15aec36fa9dc4e9d3176d409a652c7504211e7b5487fa628da9ee8369051dc3`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
