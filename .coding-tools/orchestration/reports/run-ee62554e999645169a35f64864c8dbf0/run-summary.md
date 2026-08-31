# Orchestration Run Summary

- Run: `ee62554e999645169a35f64864c8dbf0`
- Task: `226859f3256b420aa6cd9007ef5ed017`
- Objective: Apply the smallest lifecycle fix for the active mcp_only RUN/WAVE: AcceptedCodeActivationController must not start while a durable full-clean epoch is VERIFYING/FAILED/expired or READY-but-blocked, but RecoveryHost supervision must idempotently arm it as soon as the same durable epoch becomes READY with admission OPEN after bootstrap/finalize. Preserve bootstrap and ready-adoption authority guards. Do not create connector/discovery receipts, use raw HTTP/direct SQLite/force release, restart runtime, commit, push, deploy, or broaden scope.
- Status: **accepted**
- Started: `2026-08-30T20:15:31.649Z`
- Finished: `2026-08-31T00:31:51.853Z`

## Outcome metrics

- Waves: **4**
- Route decisions: **4**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `6a3ff0716ef84e99b97569c1fbc1b2ba` | 1 | `run_initial_objective` | `mcp_only` | `a357e1bb45a68cfaf25b8a2aa99a133ab256102c` | replanned |
| 2 | `7ac786f081e54a36b9c6ce57f337d313` | 1 | `replan_request` | `mcp_only` | `a357e1bb45a68cfaf25b8a2aa99a133ab256102c` | replanned |
| 3 | `ab348301620d48d3bea8ebc8eae07460` | 2 | `replan_request` | `mcp_only` | `a357e1bb45a68cfaf25b8a2aa99a133ab256102c` | replanned |
| 4 | `74541b9dec334a73a6f17add93357ef4` | 3 | `replan_request` | `mcp_only` | `a357e1bb45a68cfaf25b8a2aa99a133ab256102c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| d6eade995cd44fd9aa109ed19196f6b5 | 74541b9dec334a73a6f17add93357ef4 | accepted | a357e1bb45a68cfaf25b8a2aa99a133ab256102c | 38e72a1501f01cef4f043683fc6bd3928f460a4491978c79fd7851eb8c923a0d | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 32832 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 32854 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 32881 | `deterministic` | `deterministic` | explicit_request |
| 32903 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 32847 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 32874 | `SOL_REJECTED` | `ACCEPTING` | Reject exact wave because wave-2 write lease allowed only tests/recovery-host.test.js; the observed file in that lease was pre-existing dirty, while electron/services/recoveryHost.js production source from wave-1 was not durably adopted into this wave. Replan on the same RUN with an exact two-file lease and exact-byte existing-file adoption before acceptance. |
| 32896 | `SOL_REJECTED` | `ACCEPTING` | ACCEPTANCE_PROOF_REQUIRED: focused command passed but no passed proof was durably bound to this exact RUN/WAVE because it ran outside agent_workflow proof ledger. Replan must create a new wave and run exact-byte adoption plus focused checks inside one agent_workflow call. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `96`
- Chain head: `bc31868acd8777955479f2e126e7679db7e39db2513ec563fcbd58423293e6fb`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
