# Orchestration Wave 2

- Run: `c30aa0f90a9e4c508627ee691dc9875e`
- Wave: `5975e031825a4291aced101ea6073465`
- Objective: Read only the implementation and tests that define managed_job_residue and its supported remediation for exact stale RUN reconciliation. Identify whether residue can be terminalized via command_control/task_control while the runtime is live, or only through stopped-runtime maintenance. Do not modify jobs, ledger, source, Git, runtime, or services.
- Objective revision: `1`
- Objective SHA-256: `9ff4a1789d15e25178522b70e010d7b56ca27c2ba490581dfad032cd8f1da08b`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `9255f94c9beff33f8c6c53d6745a08968f5a12bb`
- Worktree fingerprint: `8e37ce49b4e1956ed036390bc8fd6202f719090e25b3a841ef4e1d71fd2ae4a4`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 42712 | 2026-09-07T02:34:27.062Z | wave_replanned |  | PREFLIGHT | reason=The prior attempt was rejected before execution because a wildcard was supplied in a path-bearing command token and failed safe path inspection. Replace wildcard path arguments with existing directory roots; keep the evidence scope and read-only objective unchanged. |
| 42713 | 2026-09-07T02:34:27.936Z | observation_span_recorded |  |  |  |
| 42714 | 2026-09-07T02:34:28.591Z | observation_span_recorded |  |  |  |
| 42715 | 2026-09-07T02:34:28.786Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 42716 | 2026-09-07T02:34:29.362Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 42717 | 2026-09-07T02:34:29.789Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 42718 | 2026-09-07T02:34:30.270Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 42719 | 2026-09-07T02:34:30.639Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 42720 | 2026-09-07T02:34:31.054Z | state_transition | READY | ROUTED | reason=route_selected |
| 42721 | 2026-09-07T02:34:31.284Z | observation_span_recorded |  |  |  |
| 42722 | 2026-09-07T02:34:31.913Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=ef034bb201b44d2a8e15f32b392b4d3e |
| 42723 | 2026-09-07T02:34:32.312Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 42724 | 2026-09-07T02:34:32.788Z | observation_span_recorded |  |  |  |
| 42725 | 2026-09-07T02:34:33.372Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=ef034bb201b44d2a8e15f32b392b4d3e |
| 42726 | 2026-09-07T02:34:34.133Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 42727 | 2026-09-07T02:34:35.888Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:1ffb9c070d1e2db5; input_fingerprint=132af55dd0372515cf2b7ab98a51ef615ab070357c6ba5371ff139a063f48422 |
| 42728 | 2026-09-07T02:34:36.571Z | managed_process_admitted |  |  | owner=default |
| 42729 | 2026-09-07T02:34:36.998Z | managed_process_started |  |  | owner=default |
| 42730 | 2026-09-07T02:34:37.700Z | managed_process_terminal |  |  | owner=default |
| 42731 | 2026-09-07T02:34:38.170Z | proof_recorded |  |  | stage_id=check:1ffb9c070d1e2db5; status=passed; cache_hit=False; input_fingerprint=132af55dd0372515cf2b7ab98a51ef615ab070357c6ba5371ff139a063f48422 |
| 42732 | 2026-09-07T02:34:38.384Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b5737061c9bbe6a5; input_fingerprint=075089fd9258ee5dc6377d415ecd8b9f26b19de65cc181b4b7908e9d92325283 |
| 42733 | 2026-09-07T02:34:38.843Z | managed_process_admitted |  |  | owner=default |
| 42734 | 2026-09-07T02:34:39.505Z | managed_process_started |  |  | owner=default |
| 42735 | 2026-09-07T02:34:40.035Z | managed_process_terminal |  |  | owner=default |
| 42736 | 2026-09-07T02:34:42.234Z | proof_recorded |  |  | stage_id=check:b5737061c9bbe6a5; status=passed; cache_hit=False; input_fingerprint=075089fd9258ee5dc6377d415ecd8b9f26b19de65cc181b4b7908e9d92325283 |
| 42737 | 2026-09-07T02:34:43.329Z | observation_span_recorded |  |  |  |
| 42738 | 2026-09-07T02:34:47.730Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 42739 | 2026-09-07T02:35:53.137Z | quality_outcome_recorded |  |  |  |
| 42740 | 2026-09-07T02:35:53.351Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 42741 | 2026-09-07T02:35:53.665Z | observation_span_recorded |  |  |  |
| 42742 | 2026-09-07T02:35:53.938Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:1ffb9c070d1e2db5 | passed | 132af55dd0372515cf2b7ab98a51ef615ab070357c6ba5371ff139a063f48422 | False | 1608 | 0 |
| check:b5737061c9bbe6a5 | passed | 075089fd9258ee5dc6377d415ecd8b9f26b19de65cc181b4b7908e9d92325283 | False | 2055 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| d454dcfea25c4034b516d36c9217c35d | accepted | 9255f94c9beff33f8c6c53d6745a08968f5a12bb | 67f529aef336553de249cccc25e08ed4f642005975ac22e70edf05d3b90464c4 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `56`
- Chain head: `141632cf510359a3f35d94fe39ff8fa4cb0ff0867c72601a7eaad68a644c0836`
