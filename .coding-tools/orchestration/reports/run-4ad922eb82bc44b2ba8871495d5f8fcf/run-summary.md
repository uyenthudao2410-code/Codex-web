# Orchestration Run Summary

- Run: `4ad922eb82bc44b2ba8871495d5f8fcf`
- Task: `415834495ac44124960a74b0695813e8`
- Objective: Continue the same post-P4-MX run after a read-only shell quoting failure. Read only the exact non-overlapping files needed to implement the already-settled patch; do not write. Preserve protected Control Panel paths untouched.
- Status: **active**
- Started: `2026-08-20T08:26:13.851Z`
- Finished: `None`

## Outcome metrics

- Waves: **3**
- Route decisions: **1**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **6**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `1db6c137e6eb4e79b06625bedd7e3efa` | `mcp_only` | `dc40d9764887bba7400dccb13ad37f5b47881841` | replanned |
| 2 | `2d74dc41c3084d2fba2ca6b50d4588d8` | `mcp_only` | `dc40d9764887bba7400dccb13ad37f5b47881841` | replanned |
| 3 | `507e6d69cfaf4c6dabdcec288d441013` | `mcp_only` | `dc40d9764887bba7400dccb13ad37f5b47881841` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 23484 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 23473 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 23478 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 23532 | `SOL_REJECTED` | `ACCEPTING` | Final acceptance review found two concrete defects: render_summary emits a garbled artifact-hash separator, and orchestration_tax treats absence of provider usage events as observed zero instead of unknown/null, violating the explicit unknown-is-not-zero evidence invariant. Replan narrowly to fix only those defects and add regression coverage; keep all other scope/invariants unchanged. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `95`
- Chain head: `b2e09af03c3d41db837e66780cea6befd0cca808e52227c990e062ba1a9e76b5`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
