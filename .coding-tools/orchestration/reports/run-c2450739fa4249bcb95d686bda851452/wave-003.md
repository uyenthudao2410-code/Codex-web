# Orchestration Wave 3

- Run: `c2450739fa4249bcb95d686bda851452`
- Wave: `e589f2aa4c9b4ea687962869a2324bdf`
- Objective: Natural #22 causal repair: prevent generic mutating-tool auto-start from archiving/replacing a failed task when that task still projects an exact nonterminal EOCL run. Preserve direct TaskStateStore.ensure_started semantics used by recovery fixtures and preserve normal replacement for terminal/no-run tasks. Add a focused stateless regression for failed presentation task plus canonical PREFLIGHT run.
- Objective revision: `2`
- Objective SHA-256: `32420ca5f62870da647fc8f61d49ce8cf51a13030bcae3eca77839498ec67821`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `5031f11af2490cd5256b29b16795e06d50e1eb7dcdb5f5ddf920e8b14ff89bef`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 47535 | 2026-09-10T10:41:05.137Z | wave_replanned |  | PREFLIGHT | reason=Wave 2 reproduced immediate pre-write BASE_DRIFT after prepare with zero source receipts. To remove the prepare-to-execute drift window, use one atomic agent_workflow run that creates the replacement wave, acquires its lease, applies the already-localized three-file patch, and runs focused proof in the same invocation. The causal source diagnosis and patch scope are unchanged; execution topology changes from split prepare/execute to single-call run. |
| 47536 | 2026-09-10T10:41:05.493Z | observation_span_recorded |  |  |  |
| 47537 | 2026-09-10T10:41:06.323Z | observation_span_recorded |  |  |  |
| 47538 | 2026-09-10T10:41:06.545Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 47539 | 2026-09-10T10:41:06.717Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 47540 | 2026-09-10T10:41:06.921Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 47541 | 2026-09-10T10:41:07.213Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 47542 | 2026-09-10T10:41:07.580Z | state_transition | READY | ROUTED | reason=route_selected |
| 47543 | 2026-09-10T10:41:08.007Z | observation_span_recorded |  |  |  |
| 47544 | 2026-09-10T10:41:09.237Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=414e8771a4cd469e9f1a480df5cf4f3a |
| 47545 | 2026-09-10T10:41:09.440Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 47546 | 2026-09-10T10:41:10.406Z | patch_surface_observed |  |  |  |
| 47547 | 2026-09-10T10:41:10.655Z | observation_span_recorded |  |  |  |
| 47548 | 2026-09-10T10:41:11.137Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=414e8771a4cd469e9f1a480df5cf4f3a |
| 47549 | 2026-09-10T10:41:11.350Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 47550 | 2026-09-10T10:41:12.173Z | proof_cache_miss |  |  | reason=cold; stage_id=check:58c086f769b93a3a; input_fingerprint=22e13e3978fd36d77169948be56faa25dd6939ad5150465e2b2a059315fd34a6 |
| 47551 | 2026-09-10T10:41:12.480Z | managed_process_admitted |  |  | owner=default |
| 47552 | 2026-09-10T10:41:12.909Z | managed_process_started |  |  | owner=default |
| 47553 | 2026-09-10T10:41:23.839Z | managed_process_terminal |  |  | owner=default |
| 47554 | 2026-09-10T10:41:24.425Z | proof_recorded |  |  | stage_id=check:58c086f769b93a3a; status=passed; cache_hit=False; input_fingerprint=22e13e3978fd36d77169948be56faa25dd6939ad5150465e2b2a059315fd34a6 |
| 47555 | 2026-09-10T10:41:24.638Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:80a1a46bd01d26a3; input_fingerprint=c9dd7d1de5991ff8a8590451c750dc98d74817fc7bef839e20604117d47287a9 |
| 47556 | 2026-09-10T10:41:24.995Z | managed_process_admitted |  |  | owner=default |
| 47557 | 2026-09-10T10:41:25.878Z | managed_process_started |  |  | owner=default |
| 47558 | 2026-09-10T10:41:26.619Z | managed_process_terminal |  |  | owner=default |
| 47559 | 2026-09-10T10:41:27.044Z | proof_recorded |  |  | stage_id=check:80a1a46bd01d26a3; status=failed; cache_hit=False; input_fingerprint=c9dd7d1de5991ff8a8590451c750dc98d74817fc7bef839e20604117d47287a9 |
| 47560 | 2026-09-10T10:41:27.519Z | observation_span_recorded |  |  |  |
| 47561 | 2026-09-10T10:41:27.807Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 47562 | 2026-09-10T10:41:27.998Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 47563 | 2026-09-10T10:41:28.346Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:58c086f769b93a3a | passed | 22e13e3978fd36d77169948be56faa25dd6939ad5150465e2b2a059315fd34a6 | False | 11843 | 0 |
| check:80a1a46bd01d26a3 | failed | c9dd7d1de5991ff8a8590451c750dc98d74817fc7bef839e20604117d47287a9 | False | 2046 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `160`
- Chain head: `407dd1e3990cec4fbc266b2d4a2e336343b34d45a602b1437588121b9a6b79b8`
