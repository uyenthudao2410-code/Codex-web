# Orchestration Run Summary

- Run: `27ecade1459347f987f2a14ba4508e6c`
- Task: `6fd8524628fc41ebbb1ed9824a660016`
- Objective: Implement the smallest control-plane repair for EOCL final acceptance: task_control action=accept must support explicit unchanged-byte acceptance attestations with path + expected SHA256, bind receipts to the current run/wave, fail closed on path/hash mismatch, leave task_state.modified_files untouched for unchanged files, preserve legacy modified-file receipts, and make operator report source clearly distinguish attestation from mutation receipt. Do not modify resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py.
- Status: **active**
- Started: `2026-08-22T03:14:22.212Z`
- Finished: `None`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **8**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `369c05298f494e1e8bd5f9f4deafbc7d` | 1 | `run_initial_objective` | `mcp_only` | `9eb05072e54ffca9576e23c2d4a4f4e14034bddc` | replanned |
| 2 | `46b60bb10c264d6bae6545fbcac6656a` | 2 | `replan_request` | `mcp_only` | `9eb05072e54ffca9576e23c2d4a4f4e14034bddc` | replanned |
| 3 | `c9f8db294d8941c496be005c1363bee5` | 3 | `replan_request` | `mcp_only` | `9eb05072e54ffca9576e23c2d4a4f4e14034bddc` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 26480 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 26504 | `deterministic` | `deterministic` | explicit_request |
| 26541 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 26497 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 26535 | `CHECK_FAILED` | `PROVING` |  |
| 26552 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `86`
- Chain head: `9d31283a5299564fb26f5a798fb4b2a4e6aeb49c2aa9fe4bca4a9d1d16eed34e`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
