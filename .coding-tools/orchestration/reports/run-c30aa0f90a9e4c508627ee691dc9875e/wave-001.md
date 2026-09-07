# Orchestration Wave 1

- Run: `c30aa0f90a9e4c508627ee691dc9875e`
- Wave: `7ff8d8303c544a3a9d0898b8c50f578a`
- Objective: Read only the implementation and tests that define managed_job_residue and its supported remediation for exact stale RUN reconciliation. Identify whether residue can be terminalized via command_control/task_control while the runtime is live, or only through stopped-runtime maintenance. Do not modify jobs, ledger, source, Git, runtime, or services.
- Objective revision: `1`
- Objective SHA-256: `9ff4a1789d15e25178522b70e010d7b56ca27c2ba490581dfad032cd8f1da08b`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9255f94c9beff33f8c6c53d6745a08968f5a12bb`
- Worktree fingerprint: `1f8ce07b6442346931cfcd2610c20047b7c341224ac9a059f7e79152adc73886`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 42687 | 2026-09-07T02:33:35.023Z | run_started |  | PREFLIGHT |  |
| 42688 | 2026-09-07T02:33:35.442Z | observation_span_recorded |  |  |  |
| 42689 | 2026-09-07T02:33:35.930Z | observation_span_recorded |  |  |  |
| 42690 | 2026-09-07T02:33:36.122Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 42691 | 2026-09-07T02:33:36.310Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 42692 | 2026-09-07T02:33:36.566Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 42693 | 2026-09-07T02:33:36.743Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 42694 | 2026-09-07T02:33:36.923Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 42695 | 2026-09-07T02:33:37.131Z | state_transition | READY | ROUTED | reason=route_selected |
| 42696 | 2026-09-07T02:33:37.374Z | observation_span_recorded |  |  |  |
| 42697 | 2026-09-07T02:33:37.867Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7f7c69bb8fc74d88b19ce5fb94d304cb |
| 42698 | 2026-09-07T02:33:38.040Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 42699 | 2026-09-07T02:33:38.438Z | observation_span_recorded |  |  |  |
| 42700 | 2026-09-07T02:33:38.716Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7f7c69bb8fc74d88b19ce5fb94d304cb |
| 42701 | 2026-09-07T02:33:38.899Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 42702 | 2026-09-07T02:33:39.256Z | proof_cache_miss |  |  | reason=cold; stage_id=check:1ffb9c070d1e2db5; input_fingerprint=34cce2401cd564c26e67023a541ff87cadb097531eb923d926ecb0dcbff5d407 |
| 42703 | 2026-09-07T02:33:39.674Z | managed_process_admitted |  |  | owner=default |
| 42704 | 2026-09-07T02:33:40.004Z | managed_process_started |  |  | owner=default |
| 42705 | 2026-09-07T02:33:40.487Z | managed_process_terminal |  |  | owner=default |
| 42706 | 2026-09-07T02:33:40.849Z | proof_recorded |  |  | stage_id=check:1ffb9c070d1e2db5; status=passed; cache_hit=False; input_fingerprint=34cce2401cd564c26e67023a541ff87cadb097531eb923d926ecb0dcbff5d407 |
| 42707 | 2026-09-07T02:33:41.016Z | proof_cache_miss |  |  | reason=cold; stage_id=check:dd5e7cf580b76985; input_fingerprint=7eca4c94f12c2c056d49a8da5801500df39f6f93ac6935fef3d27dd9d6b9ba76 |
| 42708 | 2026-09-07T02:33:41.201Z | observation_span_recorded |  |  |  |
| 42709 | 2026-09-07T02:33:41.371Z | failure_observed | PROVING | PROVING | failure_class=INVALID_ARGUMENT |
| 42710 | 2026-09-07T02:33:41.574Z | state_transition | PROVING | REPLAN | reason=INVALID_ARGUMENT; failure_class=INVALID_ARGUMENT |
| 42711 | 2026-09-07T02:33:41.750Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:1ffb9c070d1e2db5 | passed | 34cce2401cd564c26e67023a541ff87cadb097531eb923d926ecb0dcbff5d407 | False | 1229 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `56`
- Chain head: `141632cf510359a3f35d94fe39ff8fa4cb0ff0867c72601a7eaad68a644c0836`
