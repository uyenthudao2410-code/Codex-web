# Orchestration Wave 1

- Run: `b0b2eb98a5b34ea3ba0b8807ef8075a1`
- Wave: `e9da25a9a9274379901db6d8912a1056`
- Objective: Live new-machine Execution Hub acceptance only: establish one bounded orchestration context with no source changes and no provider inference. Prove ChatWeb and actual Codex Desktop thin-proxy share the same runtime, record/read a bounded handoff capsule, transfer controller ChatWeb -> Codex Desktop -> ChatWeb with fencing increments, audit integrity, then close the acceptance context. Do not modify source, Git history, services, settings, external config, or run any billed model/provider inference.
- Mode: `mcp_only`
- Base HEAD: `bf072d9bd08a14768b729c1d209367bc771633a5`
- Worktree fingerprint: `bab6857e11e8ce4c565b06921150e2bf0f9424daa571720646d439230320fc55`
- Contract fingerprint: `7c2be649eb2d90e92a0ab4f345fa89ac77f3dfc44edda6ca164d4c25be1d6733`
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1934 | 2026-08-14T12:00:32.239Z | run_started |  | PREFLIGHT |  |
| 1935 | 2026-08-14T12:00:32.589Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1936 | 2026-08-14T12:19:40.031Z | controller_transferred | PREFLIGHT | PREFLIGHT |  |
| 1937 | 2026-08-14T12:20:43.844Z | controller_transferred | PREFLIGHT | PREFLIGHT |  |
| 1938 | 2026-08-14T12:21:10.875Z | state_transition | PREFLIGHT | ABORTED | reason=New-machine live Execution Hub acceptance completed: exact thin-proxy heartbeat persisted across intervals, capsule continuity round-trip passed, controller transferred ChatWeb -> Codex Desktop -> ChatWeb with fence 1 -> 2 -> 3, and audit integrity passed. No provider inference was run. |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `5`
- Chain head: `f6c4cc6ab6c36e64a3b3cb7bbc0bdfd248f62a5e7d69e45494a1b0bd579cea27`
