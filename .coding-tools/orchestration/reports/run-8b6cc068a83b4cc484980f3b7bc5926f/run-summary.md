# Orchestration Run Summary

- Run: `8b6cc068a83b4cc484980f3b7bc5926f`
- Task: `93af15448f514d7ebdfc65676c9d6d4e`
- Objective: Adopt and prove the fully reviewed exact 16-file G6 candidate packet for Problem prl-b1fed3cdfd5203d9d9202643265865c3 revision 1. Preserve all unrelated dirty work. Run the user-specified Node/Python/module-size/diff proofs plus the exact stateless compatibility gate. Do not modify source in this wave, do not expand adoption beyond the 16 authorized paths, and fail closed if compatibility metadata or any proof is not current.
- Status: **accepted**
- Started: `2026-09-03T23:49:55.877Z`
- Finished: `2026-09-03T23:59:32.063Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **14**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `af467f916e76428e8f81fbc76e89c037` | 1 | `run_initial_objective` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | replanned |
| 2 | `231e0db7a058482a9eae06690573001b` | 2 | `replan_request` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | replanned |
| 3 | `1b277ccba2014cc3923ee42fa7949c4c` | 3 | `replan_request` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 4de733c561c343f096202ba674502ad9 | 1b277ccba2014cc3923ee42fa7949c4c | accepted | 80aceb583202ad381c25687969fb48adbf74622c | a7836054ad55e6b6eaaf4a8271dedebb7f4ac1b0fe4e19e9a3a47cdbc45f4351 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 38966 | `deterministic` | `deterministic` | explicit_request |
| 39000 | `deterministic` | `deterministic` | explicit_request |
| 39048 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 38991 | `CHECK_FAILED` | `PROVING` |  |
| 39035 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `127`
- Chain head: `3e3be516fba91908178771f3a8589dae7c4c8126bc1190789e7017acdfae4148`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
