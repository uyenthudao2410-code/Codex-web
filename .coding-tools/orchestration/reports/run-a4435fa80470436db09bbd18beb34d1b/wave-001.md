# Orchestration Wave 1

- Run: `a4435fa80470436db09bbd18beb34d1b`
- Wave: `a5cf93f4f495410f86fb07dcbb00a686`
- Objective: Harden runtime activation without touching unrelated stale Execution Hub lineages. Preserve explicit stale-run reconciliation semantics for operator calls, but make Runtime startup/workspace-switch reconciliation repair only terminal-parent lifecycle contradictions and leave stale active runs as read-only health candidates. Add loaded behavior bytecode fingerprints to workspace_context detail=full for provider attribution, patch preflight, verification workdir, stale reconciliation, routing policy, and external-review policy. Add a model-free organic ChatWeb+MCP rework summary and CLI that excludes benchmark/synthetic and explicit model-routed accepted runs, reports first-pass/repaired/replan counts, preflight-avoided failures, and TTA percentiles/multipliers. Update focused regressions. Do not call providers/reviewers, do not restart in this wave, and preserve all unrelated dirty files.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `bad57c9d90fa0c1c6a5088ba2fc19b084deedc78585833fd85e765eb42d4df8b`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4482 | 2026-08-15T05:48:20.515Z | run_started |  | PREFLIGHT |  |
| 4483 | 2026-08-15T05:48:20.682Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4484 | 2026-08-15T05:48:20.849Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4485 | 2026-08-15T05:48:21.009Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4486 | 2026-08-15T05:48:21.181Z | state_transition | READY | ROUTED | reason=route_selected |
| 4487 | 2026-08-15T05:48:21.841Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=9d8410c755d749d19f0ba776f49ac52f |
| 4488 | 2026-08-15T05:48:21.984Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4489 | 2026-08-15T05:48:22.803Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=9d8410c755d749d19f0ba776f49ac52f |
| 4490 | 2026-08-15T05:48:22.963Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4491 | 2026-08-15T05:48:23.516Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=cae8c1809ab02873a13f43bea1f3c4420b2b6e9bbf19648d20352da62deb830d |
| 4492 | 2026-08-15T05:48:37.612Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=cae8c1809ab02873a13f43bea1f3c4420b2b6e9bbf19648d20352da62deb830d |
| 4493 | 2026-08-15T05:48:37.832Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 4494 | 2026-08-15T05:48:37.978Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | cae8c1809ab02873a13f43bea1f3c4420b2b6e9bbf19648d20352da62deb830d | False | 13718 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `38`
- Chain head: `3a0435b03b4936a5154746b486690c380d1221844b2d4ae105645798e55d5866`
