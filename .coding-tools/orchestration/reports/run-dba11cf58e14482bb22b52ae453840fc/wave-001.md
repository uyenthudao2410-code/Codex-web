# Orchestration Wave 1

- Run: `dba11cf58e14482bb22b52ae453840fc`
- Wave: `6e662724a1b44ab2a85599ccb612787f`
- Objective: Implement P-MP3 shadow provider routing as recommendation/evidence only, with no automatic dispatch, orchestration route transition, controller transfer, write-lease mutation, or public MCP tool change. Add a small pure provider_routing module with strict bounded task features and deterministic recommendations aligned to current policy: deterministic mutation -> MCP deterministic; broad read-only -> OpenCode Flash; broad read-only + hard reasoning -> OpenCode Pro; localized + strong oracle -> Codex Mini; localized/bounded harder leaf -> Codex Luna; bounded/cross-file with localized evidence and normal/low latency -> Terra; high/critical risk or consequential mutation -> manual controller/deep review gate rather than OpenCode auto execution. Add idempotent shadow_route_recommended audit events keyed by canonical feature hash, recent shadow-route projection, and an internal routing_evidence projection that pairs recommendations with actual delegations and canonical UsageEvents for later cohort calibration. Expose internal /__control/hub action=shadow_route restricted to electron-panel/electron and bound to the current active task-projected nonterminal run/wave, including PREFLIGHT/READY before actual route selection. Tests must prove recommendations, idempotency, and that shadow_route leaves actual orchestration route/state/controller/write fence/provider adapter untouched. Preserve Smart-v3 8 tools, current production routing thresholds, OpenCode worker-only role, UI, settings, and service state. No provider inference, restart, commit, push, release, or deploy.
- Mode: `mcp_only`
- Base HEAD: `bc820986e383391e36d243e0252e23b0aef8d5b8`
- Worktree fingerprint: `6e2ee43951a4da2e532be220f96628cd1b420ff40c79b86de4dc2741322f2dd0`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1845 | 2026-08-14T09:57:11.275Z | run_started |  | PREFLIGHT |  |
| 1846 | 2026-08-14T09:57:11.890Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1847 | 2026-08-14T09:57:12.282Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1848 | 2026-08-14T09:57:12.598Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1849 | 2026-08-14T09:57:12.959Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1850 | 2026-08-14T09:57:13.265Z | state_transition | READY | ROUTED | reason=route_selected |
| 1851 | 2026-08-14T09:57:14.134Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=b406ba41b3644f82be165d5afd78d322 |
| 1852 | 2026-08-14T09:57:14.393Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1853 | 2026-08-14T09:57:15.328Z | failure_observed | EXECUTING | EXECUTING | failure_class=PATCH_AMBIGUOUS |
| 1854 | 2026-08-14T09:57:15.758Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=b406ba41b3644f82be165d5afd78d322 |
| 1855 | 2026-08-14T09:57:16.061Z | state_transition | EXECUTING | REPLAN | reason=PATCH_AMBIGUOUS; failure_class=PATCH_AMBIGUOUS |

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
- Events checked: `42`
- Chain head: `fd84fbb76b744abd300421a6427ff131d24e8c8a9e2a908b79e39a9175a1fefd`
