# Orchestration Run Summary

- Run: `afd57ba0d9d34a6b9b9d7b5e65775590`
- Task: `b35619ef3e0c4468a15932e666b00cfe`
- Objective: C5 material lifecycle continuation after C5 contract checkpoint fd7c90d5d2db477cbc45e7bfa280d3fc and predecessor C4 checkpoint 777480e8957941f9ade53ec06e248d55. On exact HEAD 9e752e34db745cd4fb2d0830a517910eced9c37f, prove only the current verified 1.0.0 NSIS clean silent install, isolated recovery-host authenticated health, exact isolated process cleanup, silent uninstall, and production invariants. Use C:\Users\Admin\AppData\Local\Temp\codex-web-c5-9e752e34 only. Do not normal-launch the Electron UI because that path calls Windows login-item settings. Do not touch C4 build/smoke/refresh, production profile, Recovery Supervisor, production descriptor except read-only snapshots, or the pre-existing legacy Start Menu shortcut. Preserve all repository source/evidence. No publish/tag/release/deploy; never ACK the forbidden report.
- Status: **accepted**
- Started: `2026-09-06T05:50:44.644Z`
- Finished: `2026-09-06T05:59:15.681Z`

## Outcome metrics

- Waves: **4**
- Route decisions: **4**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **7**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `df4816b01faa45b08abd2e31154a15b6` | 1 | `run_initial_objective` | `mcp_only` | `9e752e34db745cd4fb2d0830a517910eced9c37f` | replanned |
| 2 | `a154ccaf89ad4fdf968fda1a869b2d63` | 2 | `replan_request` | `mcp_only` | `9e752e34db745cd4fb2d0830a517910eced9c37f` | replanned |
| 3 | `6380d0a4c21246a6bb753bb3b12cb829` | 3 | `replan_request` | `mcp_only` | `9e752e34db745cd4fb2d0830a517910eced9c37f` | replanned |
| 4 | `1a8d87e465b14b229b47fae6485dd6cf` | 4 | `replan_request` | `mcp_only` | `9e752e34db745cd4fb2d0830a517910eced9c37f` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| b51dd665a3dc4db7ac5c73d93f160f02 | 1a8d87e465b14b229b47fae6485dd6cf | accepted | 9e752e34db745cd4fb2d0830a517910eced9c37f | 1fd81f1423b2515edc64e3639141226cdf80749c5bf57664db747b87fd20a5bc | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 41550 | `deterministic` | `deterministic` | explicit_request |
| 41578 | `deterministic` | `deterministic` | explicit_request |
| 41631 | `deterministic` | `deterministic` | explicit_request |
| 41673 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 41560 | `PERMISSION_REQUIRED` | `PROVING` |  |
| 41592 | `CHECK_FAILED` | `PROVING` |  |
| 41653 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `114`
- Chain head: `5612743aa5665c91bcb01266569110632f1972baf496a720e10100a01c621dfe`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
