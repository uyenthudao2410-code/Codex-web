# Orchestration Wave 2

- Run: `a34ff1344075431584e88c43f938f260`
- Wave: `9bbf50ef54864b24aea8563186a3545b`
- Objective: Read only the exact implementation boundaries needed to execute the final repair safely: confirm the task_control restart_runtime contract and stopped-runtime stale-run census behavior. Do not mutate source, Git, ledger, runtime, machine state, or services.
- Objective revision: `2`
- Objective SHA-256: `9e7319cc8f0bc159ffe61ad9c3913986061ca086891c7ad420c450dd1776d1ac`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `9255f94c9beff33f8c6c53d6745a08968f5a12bb`
- Worktree fingerprint: `9c83fe6cdfb6e7c4422a5f2fd8155512646bbb0ebe1b76a3166e747d5c41f9fc`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 42582 | 2026-09-07T02:27:59.530Z | wave_replanned |  | PREFLIGHT | reason=Previous evidence collection failed only because one searched source filename does not exist. The exact stale-run search itself passed and showed no Electron/Recovery Host production caller. Narrow this replan to existing Coding MCP files plus the known stopped-runtime census files, without repeating the stale-run caller search. |
| 42583 | 2026-09-07T02:27:59.757Z | observation_span_recorded |  |  |  |
| 42584 | 2026-09-07T02:28:00.148Z | observation_span_recorded |  |  |  |
| 42585 | 2026-09-07T02:28:00.310Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 42586 | 2026-09-07T02:28:00.460Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 42587 | 2026-09-07T02:28:00.635Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 42588 | 2026-09-07T02:28:00.793Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 42589 | 2026-09-07T02:28:00.952Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 42590 | 2026-09-07T02:28:01.120Z | state_transition | READY | ROUTED | reason=route_selected |
| 42591 | 2026-09-07T02:28:01.307Z | observation_span_recorded |  |  |  |
| 42592 | 2026-09-07T02:28:01.751Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=bd131ce7f56e4b9ab59b07da2db6d541 |
| 42593 | 2026-09-07T02:28:01.940Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 42594 | 2026-09-07T02:28:02.346Z | observation_span_recorded |  |  |  |
| 42595 | 2026-09-07T02:28:02.617Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=bd131ce7f56e4b9ab59b07da2db6d541 |
| 42596 | 2026-09-07T02:28:02.799Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 42597 | 2026-09-07T02:28:03.194Z | proof_cache_miss |  |  | reason=cold; stage_id=check:989be9a38b920c74; input_fingerprint=d62df88083fdc5a324f60ba89324b85d108ed364a4d5f82c5d80b5d7fa0a34ea |
| 42598 | 2026-09-07T02:28:03.490Z | managed_process_admitted |  |  | owner=default |
| 42599 | 2026-09-07T02:28:03.799Z | managed_process_started |  |  | owner=default |
| 42600 | 2026-09-07T02:28:04.205Z | managed_process_terminal |  |  | owner=default |
| 42601 | 2026-09-07T02:28:04.501Z | proof_recorded |  |  | stage_id=check:989be9a38b920c74; status=passed; cache_hit=False; input_fingerprint=d62df88083fdc5a324f60ba89324b85d108ed364a4d5f82c5d80b5d7fa0a34ea |
| 42602 | 2026-09-07T02:28:04.684Z | proof_cache_miss |  |  | reason=cold; stage_id=check:8f730756d68cbd8b; input_fingerprint=d44a28fe7e62e232aa6135702620e8fa7b6e9af07c82970e4cddca4d35e1a7c6 |
| 42603 | 2026-09-07T02:28:04.981Z | managed_process_admitted |  |  | owner=default |
| 42604 | 2026-09-07T02:28:05.260Z | managed_process_started |  |  | owner=default |
| 42605 | 2026-09-07T02:28:05.598Z | managed_process_terminal |  |  | owner=default |
| 42606 | 2026-09-07T02:28:05.849Z | proof_recorded |  |  | stage_id=check:8f730756d68cbd8b; status=failed; cache_hit=False; input_fingerprint=d44a28fe7e62e232aa6135702620e8fa7b6e9af07c82970e4cddca4d35e1a7c6 |
| 42607 | 2026-09-07T02:28:06.016Z | observation_span_recorded |  |  |  |
| 42608 | 2026-09-07T02:28:06.173Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 42609 | 2026-09-07T02:28:06.277Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 42610 | 2026-09-07T02:28:06.442Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 42611 | 2026-09-07T02:29:24.796Z | state_transition | REPLAN | ABORTED | reason=Diagnostic evidence is sufficient; stop this read-only REPLAN run without further retries because the remaining no-match check does not change the repair decision. |
| 42612 | 2026-09-07T02:29:25.261Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:989be9a38b920c74 | passed | d62df88083fdc5a324f60ba89324b85d108ed364a4d5f82c5d80b5d7fa0a34ea | False | 991 | 0 |
| check:8f730756d68cbd8b | failed | d44a28fe7e62e232aa6135702620e8fa7b6e9af07c82970e4cddca4d35e1a7c6 | False | 902 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `60`
- Chain head: `2d7928561e47924d779d575198f32af0697cfa69125580d53c6168f0a86e5760`
