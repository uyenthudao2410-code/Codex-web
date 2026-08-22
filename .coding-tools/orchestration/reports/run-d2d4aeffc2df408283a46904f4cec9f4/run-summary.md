# Orchestration Run Summary

- Run: `d2d4aeffc2df408283a46904f4cec9f4`
- Task: `9d36c05a71b94e8684731e18d27e2b0c`
- Objective: Acceptance-only closure of the already-present one-line T2.1 production repair in resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py: OrchestrationLedger.wave_objective_provenance must receive wave_id=wave_id, not unsupported wave=wave_id. Do not introduce any additional source change. Bind the current file state to a fresh focused proof using tests.test_truth_snapshot, then require separate final acceptance. The acceptance scope/receipt must exclude every unrelated dirty file and exclude all later T3/C1 work.
- Status: **aborted**
- Started: `2026-08-22T01:00:59.717Z`
- Finished: `2026-08-22T03:13:38.325Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `0c835f8b4ac24164a78765c67265d283` | 1 | `run_initial_objective` | `mcp_only` | `9eb05072e54ffca9576e23c2d4a4f4e14034bddc` | replanned |
| 2 | `56d5a2892b8644df9187fe176e4f5b9d` | 2 | `replan_request` | `mcp_only` | `9eb05072e54ffca9576e23c2d4a4f4e14034bddc` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 26420 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 26432 | `SOL_REJECTED` | `ACCEPTING` | Reject final acceptance fail-closed: the pending completion report has zero durable file receipts for the owned source file resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py. Expected source SHA256 is bf2eb8e8b7aa473689fb1fe6bacba671dd8fa319db831ffe5c6376d8e22daf14. The focused proof PASS is necessary but insufficient without a receipt binding the accepted source bytes. Preserve source unchanged and reopen a legitimate receipt-bound acceptance path; do not disturb already accepted T2 or T2.1 fixture/regression evidence. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `54`
- Chain head: `cd97e26fe19c9aac641a3dbffad09c30b0690ff6d526265574a5a276eb6c401c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
