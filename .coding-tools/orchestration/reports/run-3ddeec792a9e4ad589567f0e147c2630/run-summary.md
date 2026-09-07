# Orchestration Run Summary

- Run: `3ddeec792a9e4ad589567f0e147c2630`
- Task: `5b624045973f4a76996c27b8095fae9c`
- Objective: SESSION A read-only deterministic preflight only: create one EOCL RUN/Wave for Problem prl-b09df609d532ffe6816b85554c35621e revision 1 on exact E:\DEV\Codex-web main@9b3241ddc963a77d916edc453ea7b7e8e4ae5391. This wave is limited to C1 version-alignment verification and C2 full Python MCP test boundary. Do not run commands, do not mutate source/Git, do not build installer, do not use paid/model routes, and do not ACK completion report cf5cefca8d2f505e507929f1c8e44143c4a94c2e744c39efa1141bc448eae70c.
- Status: **active**
- Started: `2026-09-06T03:52:53.066Z`
- Finished: `None`

## Outcome metrics

- Waves: **4**
- Route decisions: **3**
- Failures observed: **3**
- REPLAN transitions: **3**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `583a3b43b00e4037ad2c2b2da3fc0fcb` | 1 | `run_initial_objective` | `mcp_only` | `9b3241ddc963a77d916edc453ea7b7e8e4ae5391` | replanned |
| 2 | `81838aca67424805b5c31c7c7955ea0f` | 2 | `replan_request` | `mcp_only` | `9b3241ddc963a77d916edc453ea7b7e8e4ae5391` | replanned |
| 3 | `b3e7fa840f14472988fecb28d54e96f1` | 3 | `replan_request` | `mcp_only` | `9b3241ddc963a77d916edc453ea7b7e8e4ae5391` | replanned |
| 4 | `6073b5e856be47968351b598f7d593fd` | 3 | `replan_request` | `mcp_only` | `9b3241ddc963a77d916edc453ea7b7e8e4ae5391` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 41317 | `deterministic` | `deterministic` | explicit_request |
| 41376 | `deterministic` | `deterministic` | explicit_request |
| 41436 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 41333 | `SOL_REJECTED` | `ACCEPTING` | C4 corrective REPLAN: packaged recovery smoke job da1e631c53d940c2806943053a25c089 terminally failed PACKAGED_USER_DATA_ISOLATION_FAILED:child_alive=false. Deterministic diagnosis proves electron/main.js unconditionally resets Electron userData to production APPDATA even when the packaged recovery child is launched with --user-data-dir=<isolated temp>; RuntimePaths therefore sees the live production recovery-host.lock, acquireRecoveryHostLock raises RECOVERY_HOST_ALREADY_RUNNING, and the child quits. Source remediation plus a focused regression oracle is required; do not retry the unchanged smoke. |
| 41369 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 41429 | `SOL_REJECTED` | `ACCEPTING` | C4 Wave 3 changed-implementation smoke job 07f0372dcd334e648a1c7cd3783c4e3d terminally failed PACKAGED_RECOVERY_MODE_MISMATCH after the original child_alive failure was removed. Deterministic diagnosis shows this is a stale oracle: recovery.ping intentionally returns only liveness/identity fields via recoveryPingStatus(), while recovery_plane_mode is exposed by the rich recovery.status/cachedHostStatus() contract. Replan to keep ping minimal, query recovery.status for the mode assertion, and add a focused regression that locks this split. Do not rerun the unchanged Wave 3 smoke. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `263`
- Chain head: `7149c09e72d121854a41a8b92e9baf22e724d6b02439bd77c368e074ed1bd0e5`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
