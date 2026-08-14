# Orchestration Wave 2

- Run: `dba11cf58e14482bb22b52ae453840fc`
- Wave: `2940a1079ef64a52855fdb53b104f325`
- Objective: Implement P-MP3 shadow provider routing as recommendation/evidence only, with no automatic dispatch, orchestration route transition, controller transfer, write-lease mutation, or public MCP tool change. Add a small pure provider_routing module with strict bounded task features and deterministic recommendations aligned to current policy: deterministic mutation -> MCP deterministic; broad read-only -> OpenCode Flash; broad read-only + hard reasoning -> OpenCode Pro; localized + strong oracle -> Codex Mini; localized/bounded harder leaf -> Codex Luna; bounded/cross-file with localized evidence and normal/low latency -> Terra; high/critical risk or consequential mutation -> manual controller/deep review gate rather than OpenCode auto execution. Add idempotent shadow_route_recommended audit events keyed by canonical feature hash, recent shadow-route projection, and an internal routing_evidence projection that pairs recommendations with actual delegations and canonical UsageEvents for later cohort calibration. Expose internal /__control/hub action=shadow_route restricted to electron-panel/electron and bound to the current active task-projected nonterminal run/wave, including PREFLIGHT/READY before actual route selection. Tests must prove recommendations, idempotency, and that shadow_route leaves actual orchestration route/state/controller/write fence/provider adapter untouched. Preserve Smart-v3 8 tools, current production routing thresholds, OpenCode worker-only role, UI, settings, and service state. No provider inference, restart, commit, push, release, or deploy.
- Mode: `mcp_only`
- Base HEAD: `bc820986e383391e36d243e0252e23b0aef8d5b8`
- Worktree fingerprint: `061dda8e9e128cdf93d19b26c4554983605c3779dcaad19aa6b05b306643838d`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1856 | 2026-08-14T09:58:56.122Z | wave_replanned |  | PREFLIGHT | reason=The initial P-MP3 run partially created the pure provider_routing.py, then failed before ledger/server/test integration because an insertion hunk used an ambiguous generic return-list context in orchestration_ledger.py. Inspection confirms only provider_routing.py exists. Materially continue with exact method-boundary anchors after list_usage_events and exact provider/server action anchors; do not recreate or alter the pure module. |
| 1857 | 2026-08-14T09:58:57.250Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1858 | 2026-08-14T09:58:57.699Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1859 | 2026-08-14T09:58:58.066Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1860 | 2026-08-14T09:58:58.431Z | state_transition | READY | ROUTED | reason=route_selected |
| 1861 | 2026-08-14T09:58:59.601Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3762be7e56a040cbb88a2e458eb2a885 |
| 1862 | 2026-08-14T09:58:59.883Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1863 | 2026-08-14T09:59:01.434Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3762be7e56a040cbb88a2e458eb2a885 |
| 1864 | 2026-08-14T09:59:01.807Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1865 | 2026-08-14T09:59:03.216Z | proof_recorded |  |  | stage_id=check:983b6756ab21e193; status=passed; cache_hit=False; input_fingerprint=74749e1a3a9fb3a42b36aacfecfbe0ff4ee5645b3b3dc128a5ef443f0da17cce |
| 1866 | 2026-08-14T09:59:04.275Z | proof_recorded |  |  | stage_id=check:94eeb1ff6043e00f; status=passed; cache_hit=False; input_fingerprint=bb4c04049417739a1142cafdeccfdd634184760ae37d9e968c0d57b01b73995d |
| 1867 | 2026-08-14T09:59:04.938Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 1868 | 2026-08-14T09:59:21.114Z | failure_observed | ACCEPTING | ACCEPTING | reason=Implementation compiles and pure routing tests pass, but final acceptance requires focused proof that the internal shadow_route action is idempotent and cannot mutate actual orchestration route/state, controller lease, write fence, or dispatch a provider, plus ledger routing-evidence projection coverage. Add only those missing tests and rerun affected regressions.; failure_class=SOL_REJECTED |
| 1869 | 2026-08-14T09:59:21.475Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:983b6756ab21e193 | passed | 74749e1a3a9fb3a42b36aacfecfbe0ff4ee5645b3b3dc128a5ef443f0da17cce | False | 298 | 0 |
| check:94eeb1ff6043e00f | passed | bb4c04049417739a1142cafdeccfdd634184760ae37d9e968c0d57b01b73995d | False | 231 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `25`
- Chain head: `b1fa1addc536ef7f7c1c1350b6e487c1722410e99a6a38323801d6da7a332e37`
