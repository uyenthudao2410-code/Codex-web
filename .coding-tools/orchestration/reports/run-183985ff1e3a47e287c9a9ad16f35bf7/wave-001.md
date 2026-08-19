# Orchestration Wave 1

- Run: `183985ff1e3a47e287c9a9ad16f35bf7`
- Wave: `218964d6c62b46e19c36fcc3407bd73b`
- Objective: Remove the final dead legacy measuredUsage helper from renderer/dashboard.js and update the focused dashboard regression so the helper must be absent while renderAll remains locked to canonicalMeasuredUsage. Preserve all unrelated WIP and canonical token semantics. No restart, commit, push, or live activation.
- Mode: `mcp_only`
- Base HEAD: `17fcaa360fe4e8d8f5305574b5eb9c2243fd0a02`
- Worktree fingerprint: `8c4db7a355a8006c9541a115c90f7941750775ff343fb7b32e68f20f7c971ac7`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21696 | 2026-08-19T11:34:11.638Z | run_started |  | PREFLIGHT |  |
| 21697 | 2026-08-19T11:34:12.603Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21698 | 2026-08-19T11:35:03.681Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 21699 | 2026-08-19T11:35:03.812Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 21700 | 2026-08-19T11:35:04.001Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 21701 | 2026-08-19T11:35:04.211Z | state_transition | READY | ROUTED | reason=route_selected |
| 21702 | 2026-08-19T11:35:04.786Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=b3bed922390745eaa4da3b9ef2ff93d1 |
| 21703 | 2026-08-19T11:35:04.925Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 21704 | 2026-08-19T11:35:05.425Z | patch_surface_observed |  |  |  |
| 21705 | 2026-08-19T11:35:05.636Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=b3bed922390745eaa4da3b9ef2ff93d1 |
| 21706 | 2026-08-19T11:35:05.824Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 21707 | 2026-08-19T11:35:06.319Z | proof_cache_miss |  |  | reason=cold; stage_id=check:d3e764597ea65558; input_fingerprint=6ec84be79c0d2edbbcd67636ef10be92c201f1c90abd3ea08b58d985f552cb9e |
| 21708 | 2026-08-19T11:35:06.941Z | managed_process_admitted |  |  | owner=default |
| 21709 | 2026-08-19T11:35:07.377Z | managed_process_started |  |  | owner=default |
| 21710 | 2026-08-19T11:35:07.938Z | managed_process_terminal |  |  | owner=default |
| 21711 | 2026-08-19T11:35:08.768Z | proof_recorded |  |  | stage_id=check:d3e764597ea65558; status=failed; cache_hit=False; input_fingerprint=6ec84be79c0d2edbbcd67636ef10be92c201f1c90abd3ea08b58d985f552cb9e |
| 21712 | 2026-08-19T11:35:08.946Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 21713 | 2026-08-19T11:35:09.216Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 21714 | 2026-08-19T11:35:09.403Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:d3e764597ea65558 | failed | 6ec84be79c0d2edbbcd67636ef10be92c201f1c90abd3ea08b58d985f552cb9e | False | 2018 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `44`
- Chain head: `14148f67c4fde5dee121842e53922204df88e42735f56718d7601e90544c2f3c`
