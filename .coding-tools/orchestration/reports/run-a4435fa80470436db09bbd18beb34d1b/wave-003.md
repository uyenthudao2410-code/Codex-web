# Orchestration Wave 3

- Run: `a4435fa80470436db09bbd18beb34d1b`
- Wave: `8f53d90637c1458aace5d0699f42c7c5`
- Objective: Harden runtime activation without touching unrelated stale Execution Hub lineages. Preserve explicit stale-run reconciliation semantics for operator calls, but make Runtime startup/workspace-switch reconciliation repair only terminal-parent lifecycle contradictions and leave stale active runs as read-only health candidates. Add loaded behavior bytecode fingerprints to workspace_context detail=full for provider attribution, patch preflight, verification workdir, stale reconciliation, routing policy, and external-review policy. Add a model-free organic ChatWeb+MCP rework summary and CLI that excludes benchmark/synthetic and explicit model-routed accepted runs, reports first-pass/repaired/replan counts, preflight-avoided failures, and TTA percentiles/multipliers. Update focused regressions. Do not call providers/reviewers, do not restart in this wave, and preserve all unrelated dirty files.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `ae09845a353ee8ddb342319c62d19d9e22d8a7464ae1182bc28d7e612ba905dc`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4507 | 2026-08-15T05:49:55.867Z | wave_replanned |  | PREFLIGHT | reason=The prior replan applied the durable-delegation classifier fix, then failed before proof execution because the verification command used '> NUL', which MCP correctly rejected as an unsafe command-path token. Remove redirection and execute the proof directly; implementation strategy is unchanged because the failure was proof-command syntax after the source correction. |
| 4508 | 2026-08-15T05:49:56.090Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4509 | 2026-08-15T05:49:56.320Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4510 | 2026-08-15T05:49:56.517Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 4511 | 2026-08-15T05:49:56.680Z | state_transition | READY | ROUTED | reason=route_selected |
| 4512 | 2026-08-15T05:49:57.293Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c7f99396e622444e932c34bc6f3e77da |
| 4513 | 2026-08-15T05:49:57.487Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4514 | 2026-08-15T05:49:58.126Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c7f99396e622444e932c34bc6f3e77da |
| 4515 | 2026-08-15T05:49:58.359Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4516 | 2026-08-15T05:49:58.861Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=a203e16a373bd3d29abf29fd4e05d0f26b4337e443b64078188a8db58f57b8c5 |
| 4517 | 2026-08-15T05:50:15.176Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=a203e16a373bd3d29abf29fd4e05d0f26b4337e443b64078188a8db58f57b8c5 |
| 4518 | 2026-08-15T05:50:15.374Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4519 | 2026-08-15T05:51:24.837Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | a203e16a373bd3d29abf29fd4e05d0f26b4337e443b64078188a8db58f57b8c5 | False | 15922 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| d6d5c6d8c4fd49f0b53dca8170445f43 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 235c1eec3b4adceaae0c53a052e72e23c37b634cf5930d2722c829a9f12f0d21 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `38`
- Chain head: `3a0435b03b4936a5154746b486690c380d1221844b2d4ae105645798e55d5866`
