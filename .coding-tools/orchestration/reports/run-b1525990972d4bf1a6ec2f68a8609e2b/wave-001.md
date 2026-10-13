# Orchestration Wave 1

- Run: `b1525990972d4bf1a6ec2f68a8609e2b`
- Wave: `027d6eb3efa9484f98e2b53af0189665`
- Objective: Apply one owner-approved exact local patch.
- Objective revision: `1`
- Objective SHA-256: `4eeedbc0220f5e63e04e69598363e92378f3246e371efb9cf5ca46f2a66b7555`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7999c4151cb501db86f2e4d0a2275d33fc248324`
- Worktree fingerprint: `42369ccbcbf6a1cde1ae0188d4b9e43f0cfa3a54eb9cf8d9b0db4c751f420253`
- Contract fingerprint: `4f560912731a403abaca7d7f6bc2cc5e801f4e2920909fc2482933c84edf9b96`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 60407 | 2026-10-12T17:07:20.952Z | run_started |  | PREFLIGHT |  |
| 60408 | 2026-10-12T17:07:21.301Z | observation_span_recorded |  |  |  |
| 60409 | 2026-10-12T17:07:21.523Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 60410 | 2026-10-12T17:07:21.730Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 60411 | 2026-10-12T17:07:21.923Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 60412 | 2026-10-12T17:07:22.149Z | state_transition | READY | ROUTED | reason=route_selected |
| 60413 | 2026-10-12T17:07:22.424Z | observation_span_recorded |  |  |  |
| 60414 | 2026-10-12T17:07:23.131Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=d12948a85b744118b077a6c182933e12 |
| 60415 | 2026-10-12T17:07:23.321Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 60416 | 2026-10-12T17:07:24.397Z | patch_surface_observed |  |  |  |
| 60417 | 2026-10-12T17:07:24.706Z | observation_span_recorded |  |  |  |
| 60418 | 2026-10-12T17:07:25.046Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=d12948a85b744118b077a6c182933e12 |
| 60419 | 2026-10-12T17:07:25.283Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 60420 | 2026-10-12T17:07:26.656Z | observation_span_recorded |  |  |  |
| 60421 | 2026-10-12T17:07:26.810Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 60422 | 2026-10-12T17:07:27.063Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 60649 | 2026-10-12T19:08:32.183Z | controller_transferred | ACCEPTING | ACCEPTING |  |
| 60650 | 2026-10-12T19:08:33.396Z | observation_span_recorded |  |  |  |
| 60651 | 2026-10-12T19:08:33.590Z | failure_observed | ACCEPTING | ACCEPTING | reason=Original exact patch and readback passed; this original wave has no independently executed proof. Preserve patch and replan proof only, without applying it again.; failure_class=SOL_REJECTED |
| 60652 | 2026-10-12T19:08:33.800Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 60653 | 2026-10-12T19:08:34.068Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 60992 | 2026-10-12T19:25:14.276Z | controller_transferred | REPLAN | REPLAN |  |

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
- Events checked: `50`
- Chain head: `3c60ae568d58c1bdb3b8d744efcb3f125fd997e05641bbd8e5e47a5be4dfdb0b`
