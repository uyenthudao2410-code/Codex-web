# Orchestration Run Summary

- Run: `ed50decef66646f6a1e2e777f1228954`
- Task: `79086fbfc5df48cfa852bb2ecc498b3e`
- Objective: Implement ChatWeb exact token-usage ingress only. Inspect current source and produce the smallest causal patch: accept one namespaced controller usage object from tools/call params._meta only for ChatWeb identity; validate it before dispatch via usage_event_from_controller_report semantics; for an already-active scoped run/wave require current controller lease and record before business dispatch; for the first agent_workflow request validate before dispatch then bind/claim and record after that call creates a run/wave; annotate JSON-RPC result._meta with recorded/duplicate status and usage_id/turn_id but never raw telemetry. Duplicate same evidence is idempotent; conflicting same turn_id fails closed. Missing telemetry remains unknown. Preserve smart-v3 8-tool public surface, isolation, pricing/ledger WIP. No dashboard/restart/commit/push.
- Status: **accepted**
- Started: `2026-08-19T09:39:29.322Z`
- Finished: `2026-08-19T09:48:50.816Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `13523ed5108b49b1b5ce17b2507748e9` | `mcp_only` | `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc` | replanned |
| 2 | `60f0de5edda84a1abedc86d8e323ce36` | `mcp_only` | `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc` | replanned |
| 3 | `68b99181913b4871916e805a7cc2346b` | `mcp_only` | `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 405c39021de24be0a3e755fb019f871f | 68b99181913b4871916e805a7cc2346b | accepted | 930d3e1e67f2b413aa32d5da99d1a01d22d0bddc | 8575c021ba7e112b9f7e36c71d5a4c04c328848bb66a43e82017a30f2f7d1dc6 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 21343 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 21363 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 21383 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 21357 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 21376 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 21393 | `RUNTIME_RESUME_REQUIRED` | `PROVING` | A non-terminal wave was recovered outside its original synchronous execution. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `70`
- Chain head: `336f83fdf2e69e728398753d4f78f33b8d9053e620656fa659198167d46072da`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
