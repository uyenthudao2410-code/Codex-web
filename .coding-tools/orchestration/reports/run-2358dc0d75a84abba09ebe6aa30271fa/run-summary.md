# Orchestration Run Summary

- Run: `2358dc0d75a84abba09ebe6aa30271fa`
- Task: `776dcfeb35244856a078c20f5970e747`
- Objective: Repair the two operator truth surfaces in E:\DEV\Codex-web: keep Loaded runtime source truthful through the existing cached Recovery Host projection, and make Operator Truth Console receive bounded truth_snapshot data from /__control/orchestration/live without full orchestration polling, Git scans, full-history scans, lease-maintenance writes, or hash-chain verification on the high-frequency path. Preserve all unrelated dirty worktree changes.
- Status: **active**
- Started: `2026-08-30T14:36:02.435Z`
- Finished: `None`

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
| 1 | `bb7575df98374d6186b84c2e203fc128` | 1 | `run_initial_objective` | `mcp_only` | `5f232e99f20873b4950d89d597989cb4c25e3404` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 32637 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 32807 | `SOL_REJECTED` | `ACCEPTING` | Reject to REPLAN because the only proof is bound to Base HEAD 5f232e99f20873b4950d89d597989cb4c25e3404 and worktree fingerprint da10672940aac133ba75cec2b00c5689d2cdca791f273f80fdbdb2170d3a76f0, while current HEAD is 9b766f241432b9b5bfa8aa75ae2f1816709a2c2d and later accepted work changed overlapping Control Center/live_control/test files. Proof is no longer exact-current and must not be reused. Preserve committed source; do not create a new RUN/WAVE. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `667ca1d3c5d94153110e2af17a04cac676909f1be24c595087113057f850e9aa`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
