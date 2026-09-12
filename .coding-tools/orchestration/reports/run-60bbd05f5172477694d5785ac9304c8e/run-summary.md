# Orchestration Run Summary

- Run: `60bbd05f5172477694d5785ac9304c8e`
- Task: `9d6d3a48d44749dcb20f964e9528a486`
- Objective: Natural #19: add fail-closed paired durable replan-reason attribution for PERMISSION_REQUIRED and PROTECTED_PATH_WRITE rework. Classify request_contract_correction only when the existing failure_observed to wave_replanned index pairing proves an avoidable filesystem-escape/parent-traversal, unsupported inline-script replacement, denied network-proof replacement, or protected-path strategy correction. Keep both failure classes unmapped by class alone and preserve all security/runtime behavior.
- Status: **active**
- Started: `2026-09-10T07:39:30.904Z`
- Finished: `None`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **7**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `4479479d6d5c42ca80d31c807cd0dac8` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `6e3e3d8520794a7898c28dd30b9693fa` | 2 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 3 | `3e57dc89da354920958e69c28334f04c` | 3 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 47136 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 47195 | `deterministic` | `deterministic` | explicit_request |
| 47236 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 47151 | `CHECK_FAILED` | `PROVING` |  |
| 47227 | `SOL_REJECTED` | `ACCEPTING` | Final acceptance is blocked only by durable provenance: the two source paths were modified in Wave 1, preserved unchanged in Wave 2, and exact SHA-256 attestation matches current bytes, but Wave 2 did not durably adopt those pre-existing dirty paths. Replan the same RUN to exact-byte adopt both current files, then prove the unchanged patch from the correct package root. No source rewrite or security-policy change is justified. |
| 47263 | `SOL_REJECTED` | `ACCEPTING` | Do not accept against stale Problem criterion N19-C3. Fresh durable P2 proof in this exact wave reports 115 total failures, 70 mapped, 45 unclassified; 10 high-confidence paired request-contract corrections (7 filesystem_escape, 2 inline_script, 1 protected_path), while 3 PERMISSION_REQUIRED correctly remain unknown. Generic CHECK_FAILED/BUILD_VERIFICATION_FAILED now total 42 and remain causally unattributed despite exact process-outcome linkage. Source bytes and tests are good; replan is required only after revising the Problem contract to match observed fail-closed evidence. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `102`
- Chain head: `93def450d2823f307469143cba916b5008e3b0bba0eacd6b421f7c4e2adb5630`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
