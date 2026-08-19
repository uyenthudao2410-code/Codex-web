# Orchestration Wave 4

- Run: `2ba52da917aa4f6cb784bf4b9d04207b`
- Wave: `27eaff7c507743d2a0af199341471980`
- Objective: Implement the bounded Execution Fabric observability fix already approved by the operator. Preserve current unrelated WIP. Add authoritative runtime activity projection to the orchestration control snapshot from existing runtime/resource state, make frontend liveness labels evidence-based rather than connector claims, make Hub state reflect idle/active/writing/delegating from real activity, keep Writer and provider lane semantics unchanged, add a read-only managed runtime activity view, and add focused regressions. No scheduling, capacity, routing redesign, restart, commit, or push.
- Mode: `mcp_only`
- Base HEAD: `3770d71ff620725e9de7a1843e3fc595b249f6cd`
- Worktree fingerprint: `51496ef9cf57df68ba2f14f4551cd085b73149952fd7a9edc1821a8b0f7b3a8e`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21577 | 2026-08-19T10:27:11.669Z | wave_replanned |  | PREFLIGHT | reason=The prior verification wave failed only because server.py exceeded the enforced 3500-line module-size budget (3591 lines); focused Execution Hub fault tests passed 5/5. Strategy is changed from verification-only to a bounded domain extraction, preserving behavior and avoiding any budget increase. |
| 21578 | 2026-08-19T10:27:12.521Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21579 | 2026-08-19T10:29:28.046Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 21580 | 2026-08-19T10:29:28.208Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 21581 | 2026-08-19T10:29:28.364Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 21582 | 2026-08-19T10:29:28.499Z | state_transition | READY | ROUTED | reason=route_selected |
| 21583 | 2026-08-19T10:29:29.033Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e6d96f37093e4962b5b529ef2c9be418 |
| 21584 | 2026-08-19T10:29:29.190Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 21585 | 2026-08-19T10:29:29.697Z | patch_surface_observed |  |  |  |
| 21586 | 2026-08-19T10:29:29.984Z | patch_surface_observed |  |  |  |
| 21587 | 2026-08-19T10:29:30.336Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e6d96f37093e4962b5b529ef2c9be418 |
| 21588 | 2026-08-19T10:29:30.525Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 21589 | 2026-08-19T10:29:30.979Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=6366a65686a622c36baf5465d2cfa1a8e09fa07d7a978816735ef4d674b97e71 |
| 21590 | 2026-08-19T10:29:31.333Z | managed_process_admitted |  |  | owner=default |
| 21591 | 2026-08-19T10:29:31.648Z | managed_process_started |  |  | owner=default |
| 21592 | 2026-08-19T10:29:40.538Z | managed_process_terminal |  |  | owner=default |
| 21593 | 2026-08-19T10:29:40.831Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=6366a65686a622c36baf5465d2cfa1a8e09fa07d7a978816735ef4d674b97e71 |
| 21594 | 2026-08-19T10:29:41.006Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 21595 | 2026-08-19T10:29:41.197Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 21596 | 2026-08-19T10:29:41.334Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 6366a65686a622c36baf5465d2cfa1a8e09fa07d7a978816735ef4d674b97e71 | False | 9547 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `88`
- Chain head: `fc187f0b36a84ef262a43a9b2aaa041d577dcd4f2a05ecf12a12408fb86e5ad5`
