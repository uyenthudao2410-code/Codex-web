# Orchestration Run Summary

- Run: `e114060774f54b3185a3e73963d44c43`
- Task: `861424ad5f6349deb260c7d80cd79e8d`
- Objective: Fix Recovery Host replacement startup ordering. Two live activation attempts began with recoveryTunnelCandidatePid=0, then replacement failed within ~0.2s as RECOVERY_TUNNEL_CANDIDATE_LEGACY_MIGRATION_UNVERIFIED, proving the replacement path creates a recovery tunnel candidate before legacy ownership preflight. Localize RecoveryHost.start ordering, RecoveryPlaneService start/ensureTunnel candidate creation, and existing replacement/migration tests. Preserve existing one-time same-install legacy migration and foreign-device fail-closed behavior. Do not modify source in prepare.
- Status: **accepted**
- Started: `2026-08-17T06:10:22.772Z`
- Finished: `2026-08-17T06:15:25.686Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **6**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `dfff89eca91d4a2cbffaa7a9187c3f65` | `mcp_only` | `4e5a5165e063b1b1816ef438babb19ca38d379d4` | replanned |
| 2 | `fc2df36aed2e44d88a6aa59d5ee8ffd2` | `mcp_only` | `4e5a5165e063b1b1816ef438babb19ca38d379d4` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 82f05cdd611442188d5d1e8abb859c83 | fc2df36aed2e44d88a6aa59d5ee8ffd2 | accepted | 4e5a5165e063b1b1816ef438babb19ca38d379d4 | c36751474ba4733afb720c37313beac6131fed8d65bd4de6427e9f0ff78a36b6 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 11694 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 11721 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 11715 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `0e64ef7fecde779d3bc45a89158a8730ba06fad438db958c35f3c30e3a59fc7e`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
