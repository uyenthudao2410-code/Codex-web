# Orchestration Wave 2

- Run: `a4435fa80470436db09bbd18beb34d1b`
- Wave: `daf6a17e12ce470fa061ec82e3380b79`
- Objective: Harden runtime activation without touching unrelated stale Execution Hub lineages. Preserve explicit stale-run reconciliation semantics for operator calls, but make Runtime startup/workspace-switch reconciliation repair only terminal-parent lifecycle contradictions and leave stale active runs as read-only health candidates. Add loaded behavior bytecode fingerprints to workspace_context detail=full for provider attribution, patch preflight, verification workdir, stale reconciliation, routing policy, and external-review policy. Add a model-free organic ChatWeb+MCP rework summary and CLI that excludes benchmark/synthetic and explicit model-routed accepted runs, reports first-pass/repaired/replan counts, preflight-avoided failures, and TTA percentiles/multipliers. Update focused regressions. Do not call providers/reviewers, do not restart in this wave, and preserve all unrelated dirty files.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `9f10f73168aae8a702a232430596441e103c5d792adc9fba31fe7c2f4543e50a`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4495 | 2026-08-15T05:49:26.636Z | wave_replanned |  | PREFLIGHT | reason=Focused proof showed the candidate-route filter used a derived route_selected event projection, while the durable delegation table already contained route_resolved=mini. Switch the classifier to direct durable delegation evidence so explicit candidate runs cannot leak into organic ChatWeb+MCP baseline. |
| 4496 | 2026-08-15T05:49:26.821Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4497 | 2026-08-15T05:49:26.978Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4498 | 2026-08-15T05:49:27.150Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4499 | 2026-08-15T05:49:27.311Z | state_transition | READY | ROUTED | reason=route_selected |
| 4500 | 2026-08-15T05:49:27.933Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=2a57ed16a95846399de78ca9be3b71f6 |
| 4501 | 2026-08-15T05:49:28.151Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4502 | 2026-08-15T05:49:28.887Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=2a57ed16a95846399de78ca9be3b71f6 |
| 4503 | 2026-08-15T05:49:29.143Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4504 | 2026-08-15T05:49:29.634Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=f49524cb28dfad567bbf3a7847b7bce764bd042e0c157c8348a3b52d06ffd68d |
| 4505 | 2026-08-15T05:49:29.816Z | failure_observed | PROVING | PROVING | failure_class=INVALID_ARGUMENT |
| 4506 | 2026-08-15T05:49:29.979Z | state_transition | PROVING | REPLAN | reason=INVALID_ARGUMENT; failure_class=INVALID_ARGUMENT |

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
- Events checked: `38`
- Chain head: `3a0435b03b4936a5154746b486690c380d1221844b2d4ae105645798e55d5866`
