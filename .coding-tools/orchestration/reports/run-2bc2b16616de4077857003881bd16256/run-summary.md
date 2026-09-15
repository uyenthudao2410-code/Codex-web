# Orchestration Run Summary

- Run: `2bc2b16616de4077857003881bd16256`
- Task: `17f84fb47138456ea617df92a5a66781`
- Objective: C01/M02 machine-A packaged Recovery Supervisor transition for Problem prl-22e670302757c9b7663170e226ed7c26 rev1. The fresh persistent acceptance candidate is now checkpointed and installed at %LOCALAPPDATA%\WebMcpAcceptance-1.0.0 with executable SHA256 cf9235c1398d009762e9de5b25588e7fa85347a075ff6f18f2c4a5712558827c and recovery-supervisor.ps1 SHA256 9f6cd06422484cb4911ea47c822dd6e4c5040dc6647ce283bb024b7b861a0dab. Transition the independent Recovery Supervisor from current development mode to packaged mode using the installed candidate's supervisor script and executable. Before mutation, prove current manifest mode=development, supervisor state=healthy, Scheduled Task exists, and live Recovery Host owner PID/instance are healthy. Invoke only the installed supervisor's -Action Install -Packaged with Executable=<acceptance root>\Coding Tools MCP.exe and AppRoot=<acceptance root>. Postconditions must prove: installed supervisor manifest mode=packaged; executable/app_root exact; arguments exactly ['--recovery-host']; executable SHA and installed script/launcher hashes exact; stop.request absent; Scheduled Task action uses direct Windows PowerShell on the installed supervisor script with same-user Interactive/Limited principal and AtLogOn plus one-minute repetition semantics; supervisor state healthy with live supervisor PID; Recovery Host owner PID and instance_id exactly unchanged from pre-transition; status last_host_pid/last_host_instance_id match that host; last_spawned_pid is null, proving adoption instead of spawn. If transition or any postcondition fails after mutation, rollback to development supervisor from E:\DEV\Codex-web\resources\recovery-supervisor\recovery-supervisor.ps1 using E:\DEV\Codex-web\node_modules\electron\dist\electron.exe and AppRoot E:\DEV\Codex-web, then verify development health. Do not reboot/logoff/restart runtime, edit repository source, commit, push, release, publish, or deploy.
- Status: **accepted**
- Started: `2026-09-15T09:05:07.136Z`
- Finished: `2026-09-15T09:38:36.279Z`

## Outcome metrics

- Waves: **5**
- Route decisions: **5**
- Failures observed: **4**
- REPLAN transitions: **4**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `ad40dc80d3f949c2b3d3cd32ae698bcd` | 1 | `run_initial_objective` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 2 | `2f965333e7da48b5bb5aab22ffe9c44e` | 2 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 3 | `39aac8e32ace4528928a59a8957c234d` | 3 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 4 | `e0a22fe1bcee4eb0b7d29c851d0ea38e` | 4 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 5 | `870b8f57db2345ae959422d568998d43` | 5 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 6c821be1d56f4db196d8c2f5032c8cfd | 870b8f57db2345ae959422d568998d43 | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | b3a2b1dc2476668503adce8f62a3b0f2d2951443c712da972da4bc9a6daca409 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 58713 | `deterministic` | `deterministic` | explicit_request |
| 58756 | `deterministic` | `deterministic` | explicit_request |
| 58805 | `deterministic` | `deterministic` | explicit_request |
| 58838 | `deterministic` | `deterministic` | explicit_request |
| 58916 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 58723 | `PERMISSION_REQUIRED` | `PROVING` |  |
| 58770 | `CHECK_FAILED` | `PROVING` |  |
| 58819 | `CHECK_FAILED` | `PROVING` |  |
| 58857 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `126`
- Chain head: `a1b6c357935ccb198a60f090f208d3c0dbec36c62138d7762fa8ed0a545815c5`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
