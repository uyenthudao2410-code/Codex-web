# Orchestration Run Summary

- Run: `c939fa550f344c94b4f30352fe2cefe4`
- Task: `0dcdf0fb9e8a41a88019201fd57d866e`
- Objective: C01/M02 host-side packaged installation acceptance. Using the already accepted installer identity SHA-256 a2b6fe2d168af983e5a21c461453593f71be3b5609d14172b770fb5d3155d887 and exact packaged Recovery Supervisor SHA-256 9f6cd06422484cb4911ea47c822dd6e4c5040dc6647ce283bb024b7b861a0dab, run the NSIS installer silently from a real Windows Scheduled Task host context into E:\WebMcpAcceptanceHost-1.0.0, prove the installed executable and packaged supervisor are host-visible and exact, then install the packaged Recovery Supervisor from that host-visible root via another Scheduled Task. Final fileless host probe must prove manifest mode/executable/app_root/hash, fresh capability-bearing healthy supervisor heartbeat with live supervisor PID, the canonical Recovery Host PID+instance unchanged from pre-install, and the Recovery Supervisor scheduled task present. Fail closed before reboot on any mismatch. Do not edit source, reboot, commit, push, release, publish, or deploy in this wave.
- Status: **active**
- Started: `2026-09-15T10:37:37.231Z`
- Finished: `None`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `2d052b9da7ac458e860d69c7709ca25d` | 1 | `run_initial_objective` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 2 | `148aed32b3c541fcbe66a38fbf114e22` | 2 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 59528 | `deterministic` | `deterministic` | explicit_request |
| 59553 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 59538 | `RUNTIME_RESUME_REQUIRED` | `PROVING` | A non-terminal wave was recovered outside its original synchronous execution. |
| 59567 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `44`
- Chain head: `8092f99f4f279fdfe4e7d4e31456ebc6d0f781bb7fac331d1322305d573acfa9`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
