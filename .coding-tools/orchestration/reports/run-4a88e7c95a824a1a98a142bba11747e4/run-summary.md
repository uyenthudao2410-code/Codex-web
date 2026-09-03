# Orchestration Run Summary

- Run: `4a88e7c95a824a1a98a142bba11747e4`
- Task: `6442b05474734f55a81872693585dc93`
- Objective: Continue exact RUN 321da27a9dd24556abd9e7da8632d0eb, current REPLAN wave 59aae429531941aeb09c9d7831203511, without source mutation. Recapture SHA-256 for only coordination.py and test_operator_report_isolation.py, then run exactly once the single regression test_exact_terminal_get_materializes_missing_report_without_making_audit_write to recover the concrete failure evidence after the retained command output was unavailable. Do not run the prior focused group and do not modify any file.
- Status: **aborted**
- Started: `2026-09-02T07:56:18.747Z`
- Finished: `2026-09-02T07:58:38.360Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `2c2c35d6bf044aed96d2f93b15688db5` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 35561 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 35576 | `INVALID_ARGUMENT` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `24`
- Chain head: `98a6861b01b7f3e352198c8999ae179bc313064e4539b5669bb7d7ae9d48f512`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
