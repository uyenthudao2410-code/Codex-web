# Orchestration Run Summary

- Run: `97931800eda44bee805c8aece3e1033f`
- Task: `97841b6ecdd24b95b15c9fb13063d75c`
- Objective: Diagnose the single failing T2.1 TruthSnapshot integration regression after the call-site change from unsupported wave= to wave_id=. Read only the current source and tests; identify the exact likely failing assertion/setup and the smallest corrective change. Do not mutate files, do not run package/release/restart, and do not expand beyond resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py, truth_snapshot.py, orchestration_ledger.py, orchestration_control.py, and resources/coding-tools-mcp/tests/test_truth_snapshot.py plus any directly referenced test helper.
- Status: **accepted**
- Started: `2026-08-21T08:17:32.781Z`
- Finished: `2026-08-21T20:27:29.157Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `ca5e6e06cbd84ffba25b7469b1b3cfd1` | 1 | `run_initial_objective` | `mcp_only` | `9eb05072e54ffca9576e23c2d4a4f4e14034bddc` | replanned |
| 2 | `ce3b69eda5cf413a9d9fe18282063ec4` | 2 | `replan_request` | `mcp_only` | `9eb05072e54ffca9576e23c2d4a4f4e14034bddc` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 315b3bab8e7c4eb1bf8a58d7f702a8cc | ce3b69eda5cf413a9d9fe18282063ec4 | accepted | 9eb05072e54ffca9576e23c2d4a4f4e14034bddc | acc2f3333bf0d8cffd9ae509cd5711986ddfa6d3e3e7bb624fca8819faf894e1 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 26322 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 26316 | `BASE_DRIFT` | `PREFLIGHT` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `91d8f90c113403e39fbfee1e99f2aa47cb9bb21ed5b3692600189c0e0e4deb65`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
