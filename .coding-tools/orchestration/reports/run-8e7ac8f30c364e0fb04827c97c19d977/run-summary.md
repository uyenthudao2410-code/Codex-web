# Orchestration Run Summary

- Run: `8e7ac8f30c364e0fb04827c97c19d977`
- Task: `0e5970d56355445c86d2ee5df5693b41`
- Objective: Fix C01 Recovery Supervisor Scheduled Task visibility for Problem prl-22e670302757c9b7663170e226ed7c26 rev1 using the live evidence just collected. Exact evidence: the same Windows user/SID and LOCALAPPDATA are reported inside and outside Scheduled Task, but the current C:\Users\Admin\AppData\Local\WebMcpRecoverySupervisor directory and accepted supervisor script are DirectoryNotFound from the Limited Scheduled Task while visible from the Coding Tools execution sandbox; ACL grants Admin FullControl, so this is filesystem projection rather than ACL denial. The same Scheduled Task can see/read %APPDATA%\web-mcp-assistant including recovery-host.json for PID 9640, and a new subfolder/marker written there by the sandbox is visible to the task (True|True). ProgramData/Public/E: are also visible, but prefer the existing per-user Roaming data root to avoid elevation and cross-user write surfaces. Make the smallest durable fix: change Get-InstallRoot to a dedicated recovery-supervisor subdirectory under Get-DataRoot (%APPDATA%\web-mcp-assistant), retain the current direct hidden Windows PowerShell Scheduled Task action, and preserve a legacy LocalApplicationData root helper only for best-effort cleanup after the replacement supervisor has published a fresh valid heartbeat. Do not delete the legacy root before new readiness is proven. Uninstall should best-effort remove both current and legacy install roots. Update the focused source contract test and RECOVERY_HOST.md operational path/visibility explanation. Do not restart runtime, install packaged candidate, reboot, build installer, commit, push, release, or deploy in this wave.
- Status: **accepted**
- Started: `2026-09-15T07:35:16.324Z`
- Finished: `2026-09-15T08:02:27.047Z`

## Outcome metrics

- Waves: **6**
- Route decisions: **6**
- Failures observed: **5**
- REPLAN transitions: **5**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `7176830452e949eeacb9e0085fd10b62` | 1 | `run_initial_objective` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 2 | `4a6f9f229c72435994fd08e65b5d056a` | 2 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 3 | `aa84f7a11b45449582e7d21781785a40` | 3 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 4 | `63e44ad0f1184917970a26b0ba6122be` | 4 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 5 | `fa9e74ba4b82446598647cc6d45a0ebe` | 5 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 6 | `cc09c3270d994fb9b8e7bb52555f7872` | 6 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 4eb54590815c4b7b899ea9d0f5eedc4d | cc09c3270d994fb9b8e7bb52555f7872 | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | 3cc202d78e6d4c50e6edb77dac23cdad242d7f6bf6725cdd8720d171e81cc8fc | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 57816 | `deterministic` | `deterministic` | explicit_request |
| 57888 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 57911 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 57988 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 58084 | `deterministic` | `deterministic` | explicit_request |
| 58147 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 57847 | `SOL_REJECTED` | `ACCEPTING` | Rejecting this wave because it ran focused tests successfully but produced no requested source mutation: affected_files=[], patch_results=[], and completion_report.what_changed.files=[] while the supervisor still uses the old LocalApplicationData install root. Tests against unchanged source do not prove the Roaming install-root fix. |
| 57894 | `SOURCE_DRIFT` | `EXECUTING` |  |
| 57928 | `CHECK_FAILED` | `PROVING` |  |
| 58042 | `SOL_REJECTED` | `ACCEPTING` | Replan required only for acceptance lineage: recovery-supervisor.ps1 was pre-existing dirty at this wave start and therefore was not proven inside this wave's write lease. The focused tests are green, but source bytes must be exact-byte adopted into a new wave before controller acceptance. |
| 58087 | `BASE_DRIFT` | `ROUTED` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `157`
- Chain head: `9f60fdae5283de9c93f97921c9edbdd993758d31b935a527da1eeff6f051481f`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
