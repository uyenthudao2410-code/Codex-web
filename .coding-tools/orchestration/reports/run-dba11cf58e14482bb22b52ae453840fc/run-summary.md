# Orchestration Run Summary

- Run: `dba11cf58e14482bb22b52ae453840fc`
- Task: `9367f38e81c1445880bcbe30fce2d268`
- Objective: Implement P-MP3 shadow provider routing as recommendation/evidence only, with no automatic dispatch, orchestration route transition, controller transfer, write-lease mutation, or public MCP tool change. Add a small pure provider_routing module with strict bounded task features and deterministic recommendations aligned to current policy: deterministic mutation -> MCP deterministic; broad read-only -> OpenCode Flash; broad read-only + hard reasoning -> OpenCode Pro; localized + strong oracle -> Codex Mini; localized/bounded harder leaf -> Codex Luna; bounded/cross-file with localized evidence and normal/low latency -> Terra; high/critical risk or consequential mutation -> manual controller/deep review gate rather than OpenCode auto execution. Add idempotent shadow_route_recommended audit events keyed by canonical feature hash, recent shadow-route projection, and an internal routing_evidence projection that pairs recommendations with actual delegations and canonical UsageEvents for later cohort calibration. Expose internal /__control/hub action=shadow_route restricted to electron-panel/electron and bound to the current active task-projected nonterminal run/wave, including PREFLIGHT/READY before actual route selection. Tests must prove recommendations, idempotency, and that shadow_route leaves actual orchestration route/state/controller/write fence/provider adapter untouched. Preserve Smart-v3 8 tools, current production routing thresholds, OpenCode worker-only role, UI, settings, and service state. No provider inference, restart, commit, push, release, or deploy.
- Status: **accepted**
- Started: `2026-08-14T09:57:10.588Z`
- Finished: `2026-08-14T10:01:23.711Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **8**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `6e662724a1b44ab2a85599ccb612787f` | `mcp_only` | `bc820986e383391e36d243e0252e23b0aef8d5b8` | replanned |
| 2 | `2940a1079ef64a52855fdb53b104f325` | `mcp_only` | `bc820986e383391e36d243e0252e23b0aef8d5b8` | replanned |
| 3 | `e65b2e07912548358195734b429c7408` | `mcp_only` | `bc820986e383391e36d243e0252e23b0aef8d5b8` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 0d9adf99903646ddb7dbcbb1817b4fe9 | e65b2e07912548358195734b429c7408 | accepted | 7609297462713beb104e5c933ea4d6bf3b24ec11 | d9ed6923c141172199000794fa5a844178a0a4374b49b6a43db8b0bd1fbc25df | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 1849 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 1859 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 1873 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 1853 | `PATCH_AMBIGUOUS` | `EXECUTING` |  |
| 1868 | `SOL_REJECTED` | `ACCEPTING` | Implementation compiles and pure routing tests pass, but final acceptance requires focused proof that the internal shadow_route action is idempotent and cannot mutate actual orchestration route/state, controller lease, write fence, or dispatch a provider, plus ledger routing-evidence projection coverage. Add only those missing tests and rerun affected regressions. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `42`
- Chain head: `fd84fbb76b744abd300421a6427ff131d24e8c8a9e2a908b79e39a9175a1fefd`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
