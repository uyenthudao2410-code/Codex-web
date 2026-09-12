# Orchestration Wave 2

- Run: `babe1bae0d534f0f8421374227adcd5a`
- Wave: `4646382c8ddc418a80c229d6b7268a96`
- Objective: Fix PRL prl-a5bf3e0510b110459e4cf57f5bcde24b: in RecoveryHost.superviseOnce, when the direct serviceSupervisorRestartRequest attempt returns status=deferred with a retained durable restart journal (notably transient RUNTIME_BUSY while the initiating task_control call is still leaving admission), do not fall through into orchestrator.supervise in the same watchdog tick because orchestrator.supervise calls serviceSupervisorRestartRequest again. Return a fail-closed transitional supervision projection for that tick; allow the next watchdog tick to retry. Add a focused regression test that reproduces deferred-first then accepted-on-next-tick ordering and proves no same-tick second consumption, no ordinary supervise/recovery/UI work on the deferred tick, and the accepted tick yields immediately for handoff. Preserve all activation fences, durable journal semantics, exact identity checks, and unrelated dirty worktree changes.
- Objective revision: `1`
- Objective SHA-256: `76cd9c22f3fc231d4ec54c83845b294f7864d67a1e989d880e0057dbd90d2950`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `6eb7d200b22c3598ba6a0b798705b597c5433b2eeeb36f59fb87f20177b620dc`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 49683 | 2026-09-11T09:25:48.075Z | wave_replanned |  | PREFLIGHT | reason=The first execution attempt was rejected before any mutation because EOCL forbids adopting and patching the same paths in one wave. No workspace bytes changed and the root cause/objective are unchanged. Continue the same RUN in a new wave using the exact prepared dirty-worktree fingerprint as the baseline and apply only the bounded two-file patch; preserve all pre-existing dirty bytes and run the focused regression oracle. |
| 49684 | 2026-09-11T09:25:48.476Z | observation_span_recorded |  |  |  |
| 49685 | 2026-09-11T09:25:48.850Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=auto; resolved=mcp_only |
| 49686 | 2026-09-11T09:25:49.042Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 49687 | 2026-09-11T09:25:49.242Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 49688 | 2026-09-11T09:25:49.445Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=auto; resolved=deterministic |
| 49689 | 2026-09-11T09:25:49.595Z | state_transition | READY | ROUTED | reason=route_selected |
| 49690 | 2026-09-11T09:25:49.804Z | observation_span_recorded |  |  |  |
| 49691 | 2026-09-11T09:25:50.718Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=62266ad3354c4678808fe334ac092606 |
| 49692 | 2026-09-11T09:25:50.976Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 49693 | 2026-09-11T09:25:51.973Z | patch_surface_observed |  |  |  |
| 49694 | 2026-09-11T09:25:52.160Z | observation_span_recorded |  |  |  |
| 49695 | 2026-09-11T09:25:52.443Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=62266ad3354c4678808fe334ac092606 |
| 49696 | 2026-09-11T09:25:52.612Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 49697 | 2026-09-11T09:25:53.411Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=775141562f9669612ae8bffb9ba8e071d71bafac5068b31ba7051ea88f725ee0 |
| 49698 | 2026-09-11T09:25:53.851Z | managed_process_admitted |  |  | owner=default |
| 49699 | 2026-09-11T09:25:54.174Z | managed_process_started |  |  | owner=default |
| 49700 | 2026-09-11T09:26:11.483Z | managed_process_terminal |  |  | owner=default |
| 49701 | 2026-09-11T09:26:12.751Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=775141562f9669612ae8bffb9ba8e071d71bafac5068b31ba7051ea88f725ee0 |
| 49702 | 2026-09-11T09:26:13.781Z | observation_span_recorded |  |  |  |
| 49703 | 2026-09-11T09:26:13.988Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 49704 | 2026-09-11T09:28:15.927Z | managed_process_admitted |  |  | owner=default |
| 49705 | 2026-09-11T09:28:16.265Z | managed_process_started |  |  | owner=default |
| 49706 | 2026-09-11T09:28:16.923Z | managed_process_terminal |  |  | owner=default |
| 49707 | 2026-09-11T09:40:14.424Z | managed_process_admitted |  |  | owner=default |
| 49708 | 2026-09-11T09:40:14.684Z | managed_process_started |  |  | owner=default |
| 49709 | 2026-09-11T09:40:15.162Z | managed_process_terminal |  |  | owner=default |
| 49710 | 2026-09-11T09:41:06.537Z | failure_observed | ACCEPTING | ACCEPTING | reason=Reject this wave as a full-Problem closure claim because its recorded proof establishes the regression oracle but does not yet establish the live handoff_drains and exact_stale_postflight criteria. Preserve the applied bytes; replan the same RUN around live controlled-restart evidence rather than fabricating a complete coverage manifest.; failure_class=SOL_REJECTED |
| 49711 | 2026-09-11T09:41:06.754Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 49712 | 2026-09-11T09:41:07.012Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 775141562f9669612ae8bffb9ba8e071d71bafac5068b31ba7051ea88f725ee0 | False | 18921 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `326`
- Chain head: `0ec6738f6d548fe6b72ddcbf21169e5517df57d43a6a365e26b7e46224cd43c8`
