# Orchestration Wave 1

- Run: `4af4b6a6240d4207b2fea6b9fe169d7f`
- Wave: `bbb9c934332f47ccbf926e486fdf90fb`
- Objective: Restore Control Center tabs: manager window must load index.html, token window stays token-dashboard.html
- Objective revision: `1`
- Objective SHA-256: `b03761fa1153a6866888ac1a80df091eb5121d75a66b29a0d4c38e3267b32e70`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `853ea5a6700669f12af2659613e6bcd636e228e3872ce9d33d613dec764c63f9`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 43766 | 2026-09-08T06:58:27.693Z | run_started |  | PREFLIGHT |  |
| 43767 | 2026-09-08T06:58:28.042Z | observation_span_recorded |  |  |  |
| 43768 | 2026-09-08T06:58:39.534Z | solution_shadow_recommended |  |  |  |
| 43769 | 2026-09-08T06:58:45.913Z | observation_span_recorded |  |  |  |
| 43770 | 2026-09-08T06:58:46.109Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 43771 | 2026-09-08T06:58:46.334Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 43772 | 2026-09-08T06:58:46.606Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=auto; resolved=mcp_only |
| 43773 | 2026-09-08T06:58:46.840Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 43774 | 2026-09-08T06:58:47.078Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 43775 | 2026-09-08T06:58:47.249Z | route_selected | READY | READY | reason=roi_gate_hold_insufficient_paired_evidence; requested=auto; resolved=deterministic |
| 43776 | 2026-09-08T06:58:47.477Z | state_transition | READY | ROUTED | reason=route_selected |
| 43777 | 2026-09-08T06:58:47.714Z | observation_span_recorded |  |  |  |
| 43778 | 2026-09-08T06:58:48.537Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4aaa8ce374c34107a221e60d7a8e8a72 |
| 43779 | 2026-09-08T06:58:48.681Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 43780 | 2026-09-08T06:58:49.371Z | observation_span_recorded |  |  |  |
| 43781 | 2026-09-08T06:58:49.686Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4aaa8ce374c34107a221e60d7a8e8a72 |
| 43782 | 2026-09-08T06:58:49.842Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 43783 | 2026-09-08T06:58:50.487Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=79bfaa457990d7d131189ee56bac09043ae8608f2f2a39cdabeb64bf31a5809c |
| 43784 | 2026-09-08T06:58:50.886Z | managed_process_admitted |  |  | owner=default |
| 43785 | 2026-09-08T06:58:51.224Z | managed_process_started |  |  | owner=default |
| 43786 | 2026-09-08T06:59:09.669Z | managed_process_terminal |  |  | owner=default |
| 43787 | 2026-09-08T06:59:18.743Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=79bfaa457990d7d131189ee56bac09043ae8608f2f2a39cdabeb64bf31a5809c |
| 43788 | 2026-09-08T06:59:18.977Z | observation_span_recorded |  |  |  |
| 43789 | 2026-09-08T06:59:19.190Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 45213 | 2026-09-09T07:41:39.149Z | failure_observed | ACCEPTING | ACCEPTING | reason=Historical non-Problem wave is still ACCEPTING from 2026-09-08, has no durable file receipts, no live owner/job/lease, and its proof source fingerprint 853ea5a6700669f12af2659613e6bcd636e228e3872ce9d33d613dec764c63f9 does not match the current worktree fingerprint c6f9071869d4882401a598b4463ab6c5b574382ead7d293a98a6e8830283b931. Reject rather than falsely accept stale proof.; failure_class=SOL_REJECTED |
| 45214 | 2026-09-09T07:41:39.308Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 45215 | 2026-09-09T07:41:39.547Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 45219 | 2026-09-09T07:43:47.186Z | state_transition | REPLAN | ABORTED | reason=Terminalize the rejected historical non-Problem RUN after stale source/provenance rejection; preserve ledger evidence and do not reopen or create another wave. |
| 45220 | 2026-09-09T07:43:47.617Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 79bfaa457990d7d131189ee56bac09043ae8608f2f2a39cdabeb64bf31a5809c | False | 27921 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `29`
- Chain head: `65fcc5190cb3675ffefe649b76bf6de2120a387f34ec1b6719f1ffed6b0378c2`
