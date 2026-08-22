# Orchestration Run Summary

- Run: `27ecade1459347f987f2a14ba4508e6c`
- Task: `6fd8524628fc41ebbb1ed9824a660016`
- Objective: Implement the smallest control-plane repair for EOCL final acceptance: task_control action=accept must support explicit unchanged-byte acceptance attestations with path + expected SHA256, bind receipts to the current run/wave, fail closed on path/hash mismatch, leave task_state.modified_files untouched for unchanged files, preserve legacy modified-file receipts, and make operator report source clearly distinguish attestation from mutation receipt. Do not modify resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py.
- Status: **accepted**
- Started: `2026-08-22T03:14:22.212Z`
- Finished: `2026-08-22T04:01:11.889Z`

## Outcome metrics

- Waves: **5**
- Route decisions: **5**
- Failures observed: **4**
- REPLAN transitions: **4**
- Proof stages: **13**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `369c05298f494e1e8bd5f9f4deafbc7d` | 1 | `run_initial_objective` | `mcp_only` | `9eb05072e54ffca9576e23c2d4a4f4e14034bddc` | replanned |
| 2 | `46b60bb10c264d6bae6545fbcac6656a` | 2 | `replan_request` | `mcp_only` | `9eb05072e54ffca9576e23c2d4a4f4e14034bddc` | replanned |
| 3 | `c9f8db294d8941c496be005c1363bee5` | 3 | `replan_request` | `mcp_only` | `9eb05072e54ffca9576e23c2d4a4f4e14034bddc` | replanned |
| 4 | `e0d5eeddf1ab4e9d8333917ce4633709` | 4 | `replan_request` | `mcp_only` | `0415538a0c8212d0d7e4b7217faad5b289020cff` | replanned |
| 5 | `43a7f9bc3e0d4df4bd4523611a6c3e55` | 5 | `replan_request` | `mcp_only` | `0415538a0c8212d0d7e4b7217faad5b289020cff` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| c008fde579d74593baf2f668ed8c9174 | 43a7f9bc3e0d4df4bd4523611a6c3e55 | accepted | 0415538a0c8212d0d7e4b7217faad5b289020cff | e4765bc066852cd574aa75455fc0e3d3c9185ad0dba60e3594768d7645b65d58 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 26480 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 26504 | `deterministic` | `deterministic` | explicit_request |
| 26541 | `deterministic` | `deterministic` | explicit_request |
| 26560 | `deterministic` | `deterministic` | explicit_request |
| 26578 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 26497 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 26535 | `CHECK_FAILED` | `PROVING` |  |
| 26552 | `CHECK_FAILED` | `PROVING` |  |
| 26571 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `141`
- Chain head: `4db1ca0f91a496b1bad885a43f3d9b998de192d05d5bd8d521657d239be34121`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
