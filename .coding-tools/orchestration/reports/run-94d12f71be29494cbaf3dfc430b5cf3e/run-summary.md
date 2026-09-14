# Orchestration Run Summary

- Run: `94d12f71be29494cbaf3dfc430b5cf3e`
- Task: `1ffc7317f42040e6b60738a29f1d9b86`
- Objective: Proof-only reconciliation of the already-installed Machine-A C01 candidate after the prior orchestration parser failure. Do not install again. Verify current persistent state only: one Coding Tools MCP uninstall registration at the normal per-user location, installed executable exists and hash is captured, no packaged process is running, HKCU Run has no Coding Tools MCP entry, production Recovery descriptor remains SHA256 90cd716495beda127cf00aaf44614ef71b7cb80471e02b1176e30e756f8941f6, and WebMCP Recovery Supervisor task XML remains SHA256 68b7d4a018fbe21c044d34a409ec09248b47198a35400d82a3bd1f552a043295. No source edits, launch, autostart enable, reboot/runtime restart, commit/push/publish/release/deploy.
- Status: **accepted**
- Started: `2026-09-14T14:10:53.156Z`
- Finished: `2026-09-14T14:11:41.569Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **6**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `d87d6d29c0a74889967ae65cbecfeaaa` | 1 | `run_initial_objective` | `mcp_only` | `ae04947d5969e9ee92bf1fe7532bf30e186f8280` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 23cfc9c9ed69490caf63591ee317c369 | d87d6d29c0a74889967ae65cbecfeaaa | accepted | ae04947d5969e9ee92bf1fe7532bf30e186f8280 | 7b73ab5e11b21e44c351b4c1947b4ce72634d71c248f4b75858d5987da0ed848 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 55468 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `56`
- Chain head: `df0f7af0a582714c4232e9b0497e481d5ec3fa05078c051fafea4d9a2b6ae92e`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
