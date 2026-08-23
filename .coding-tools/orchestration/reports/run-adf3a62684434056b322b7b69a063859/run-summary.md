# Orchestration Run Summary

- Run: `adf3a62684434056b322b7b69a063859`
- Task: `ad7054156d51437ca396764f55841183`
- Objective: Mechanically apply the already-reviewed canonical ledger gate integration only. Do not diagnose or redesign. ledger_file_gate.py already exists from the prior bounded write. Modify only OrchestrationLedger._connect and LedgerReadSession so every canonical SQLite handle holds the shared ledger_access_gate for its full lifetime. Preserve all unrelated changes. Then compile the three modules and run tests/test_ledger_analysis.py.
- Status: **accepted**
- Started: `2026-08-22T20:09:27.563Z`
- Finished: `2026-08-23T01:38:36.092Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `3a29870a9adb48f09ae4ffe17c9f0f67` | 1 | `run_initial_objective` | `deep_single_lane` | `0a9d4c1325624a85f051beabb5a9af88bae9d691` | replanned |
| 2 | `971a94efbbc045f482662ca0b1077740` | 1 | `replan_request` | `mcp_only` | `0a9d4c1325624a85f051beabb5a9af88bae9d691` | replanned |
| 3 | `7da356c8a6d84efbbfbb15266f1a29c4` | 2 | `replan_request` | `mcp_only` | `0a9d4c1325624a85f051beabb5a9af88bae9d691` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 82a134a2b2c040a88932195f526c7975 | 7da356c8a6d84efbbfbb15266f1a29c4 | accepted | 0a9d4c1325624a85f051beabb5a9af88bae9d691 | e3d116f5006ce5fd293985209e3421371507be9575bba51c0a3388ba513e72bb | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 28150 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 28168 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 28143 | `MODE_ROUTE_MISMATCH` | `PREFLIGHT` |  |
| 28162 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `47`
- Chain head: `b7330bbde58599fa37c4565f4811c256627b1a92f8da0335ef72d109b98e0432`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
