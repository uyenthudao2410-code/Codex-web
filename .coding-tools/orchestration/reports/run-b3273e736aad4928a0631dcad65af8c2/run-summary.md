# Orchestration Run Summary

- Run: `b3273e736aad4928a0631dcad65af8c2`
- Task: `05aaa42a4def45f5b0a813b0b419d2a1`
- Objective: Replacement W2 after durable control-plane context loss terminalized prior RUN 03fd5fbb0cc34177972b6065150c8f73 without Wave-3 writes. Implement exact cross-wave idempotency for ChatWeb controller usage. Controller economic usage_id must be stable for RUN + turn_id across reconnect/REPLAN waves; wave_id/delegation_id remain first-attribution metadata. Same exact controller receipt in a later wave must deduplicate without double-counting. Conflicting economic evidence for the same RUN+turn must fail closed. Generic/provider build_usage_event identity and provider dedupe semantics must remain unchanged. Preserve unknown_not_zero and unrelated dirty work. Add focused regression proof. Do not reuse prior stale proof. No commit/push/restart/package/release/deploy.
- Status: **accepted**
- Started: `2026-08-31T19:04:17.463Z`
- Finished: `2026-08-31T19:10:14.732Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `8ea0be9cb8d2498d8661bda24d157fc4` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| c4dc970d846742c28e53fc98c6f3aeb7 | 8ea0be9cb8d2498d8661bda24d157fc4 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 9263765c83e2b98ca345ee37472a87ffcfe735215a5f64ce746a464837bd3bc8 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 33645 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `1cb3f7580c257dbc2b3c6d3c37af0fd8e8f964f15fa040b2f549408cf466cc60`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
