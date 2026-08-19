# Orchestration Wave 2

- Run: `183985ff1e3a47e287c9a9ad16f35bf7`
- Wave: `244b12d5c1b64e8a9f679e1043d457af`
- Objective: Remove the final dead legacy measuredUsage helper from renderer/dashboard.js and update the focused dashboard regression so the helper must be absent while renderAll remains locked to canonicalMeasuredUsage. Preserve all unrelated WIP and canonical token semantics. No restart, commit, push, or live activation.
- Mode: `mcp_only`
- Base HEAD: `17fcaa360fe4e8d8f5305574b5eb9c2243fd0a02`
- Worktree fingerprint: `7e6c398958947ed77a72f134ff7e1dfc47e6ef0b9582d35f0d5dcc000243e528`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21715 | 2026-08-19T11:35:43.125Z | wave_replanned |  | PREFLIGHT | reason=Previous cleanup wave entered REPLAN after patch-context drift while task projection reports both target files modified and the focused dashboard test failed. Reconcile actual current source instead of replaying the stale patch; only repair the remaining mismatch. |
| 21716 | 2026-08-19T11:35:43.908Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21717 | 2026-08-19T11:35:48.280Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 21718 | 2026-08-19T11:35:48.421Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 21719 | 2026-08-19T11:35:48.594Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 21720 | 2026-08-19T11:35:48.769Z | state_transition | READY | ROUTED | reason=route_selected |
| 21721 | 2026-08-19T11:35:49.292Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=98822fbf89dc414e832e6f734411f7a2 |
| 21722 | 2026-08-19T11:35:49.469Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 21723 | 2026-08-19T11:35:49.923Z | patch_surface_observed |  |  |  |
| 21724 | 2026-08-19T11:35:50.204Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=98822fbf89dc414e832e6f734411f7a2 |
| 21725 | 2026-08-19T11:35:50.417Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 21726 | 2026-08-19T11:35:50.829Z | proof_cache_miss |  |  | reason=cold; stage_id=check:d3e764597ea65558; input_fingerprint=0ee91b4556c45c01fa1dfd474e5a780cd8eafde86784a2adf72754b1183641d4 |
| 21727 | 2026-08-19T11:35:51.219Z | managed_process_admitted |  |  | owner=default |
| 21728 | 2026-08-19T11:35:51.503Z | managed_process_started |  |  | owner=default |
| 21729 | 2026-08-19T11:35:52.019Z | managed_process_terminal |  |  | owner=default |
| 21730 | 2026-08-19T11:35:52.352Z | proof_recorded |  |  | stage_id=check:d3e764597ea65558; status=passed; cache_hit=False; input_fingerprint=0ee91b4556c45c01fa1dfd474e5a780cd8eafde86784a2adf72754b1183641d4 |
| 21731 | 2026-08-19T11:35:52.570Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=470eac11a7739b86429a917fd9dfa467f1542f765e96e2fdb3ab61c0cc95342b |
| 21732 | 2026-08-19T11:35:52.955Z | managed_process_admitted |  |  | owner=default |
| 21733 | 2026-08-19T11:35:53.235Z | managed_process_started |  |  | owner=default |
| 21734 | 2026-08-19T11:35:54.062Z | managed_process_terminal |  |  | owner=default |
| 21735 | 2026-08-19T11:35:54.335Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=470eac11a7739b86429a917fd9dfa467f1542f765e96e2fdb3ab61c0cc95342b |
| 21736 | 2026-08-19T11:35:54.854Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 21737 | 2026-08-19T11:36:08.243Z | quality_outcome_recorded |  |  |  |
| 21738 | 2026-08-19T11:36:08.461Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 21739 | 2026-08-19T11:36:08.866Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:d3e764597ea65558 | passed | 0ee91b4556c45c01fa1dfd474e5a780cd8eafde86784a2adf72754b1183641d4 | False | 1160 | 0 |
| check:466c2f308b48c766 | passed | 470eac11a7739b86429a917fd9dfa467f1542f765e96e2fdb3ab61c0cc95342b | False | 1435 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 74c59804493d4cc2b71e07896893f842 | accepted | 17fcaa360fe4e8d8f5305574b5eb9c2243fd0a02 | a0c58073ef1a60942843c1e158eb2afd6d03cf1c0ac9d9de24c9fc04ea369f40 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `44`
- Chain head: `14148f67c4fde5dee121842e53922204df88e42735f56718d7601e90544c2f3c`
