# Orchestration Wave 1

- Run: `63db31c334b84d24a4d6b7df660fa39a`
- Wave: `c945bc87c9d945339c7088e87c0faaee`
- Objective: Complete only the missing stale-health regression tests; production stale-health source changes are already present. Add candidate-before/reconciled-after assertions and a runtime projection test that proves current unresolved stale health is zero while reconciled history remains visible.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `d6ca289c0b908b9f967bfb6f2d66cee3da4f11a617720d42c873fee1a9cc80f7`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 3931 | 2026-08-15T02:54:01.125Z | run_started |  | PREFLIGHT |  |
| 3932 | 2026-08-15T02:54:01.306Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 3933 | 2026-08-15T02:54:01.511Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 3934 | 2026-08-15T02:54:01.716Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 3935 | 2026-08-15T02:54:01.938Z | state_transition | READY | ROUTED | reason=route_selected |
| 3936 | 2026-08-15T02:54:02.454Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e4adc5e88c684f52a39f69f9ce51ce9e |
| 3937 | 2026-08-15T02:54:02.687Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 3938 | 2026-08-15T02:54:03.258Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e4adc5e88c684f52a39f69f9ce51ce9e |
| 3939 | 2026-08-15T02:54:03.451Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 3940 | 2026-08-15T02:54:03.817Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=436976df5eb133586092f22db39812b545cf25a3e95c9d4307d4a225640f9736 |
| 3941 | 2026-08-15T02:54:05.848Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=436976df5eb133586092f22db39812b545cf25a3e95c9d4307d4a225640f9736 |
| 3942 | 2026-08-15T02:54:06.036Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 3943 | 2026-08-15T02:54:06.187Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 436976df5eb133586092f22db39812b545cf25a3e95c9d4307d4a225640f9736 | False | 1625 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `786b6fff7597ea59eb69b8bb42b2f9179bf1980f9e865f01490a36fe31e1f8bb`
