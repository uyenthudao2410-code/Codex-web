# Orchestration Wave 4

- Run: `2bc2b16616de4077857003881bd16256`
- Wave: `e0a22fe1bcee4eb0b7d29c851d0ea38e`
- Objective: C01/M02 machine-A packaged Recovery Supervisor transition for Problem prl-22e670302757c9b7663170e226ed7c26 rev1. Replan after wave 39aac8e32ace4528928a59a8957c234d was rejected by Windows before PowerShell execution with 'The command line is too long'; no external mutation occurred. Preserve the same exact accepted installed candidate and no-controller-network oracle, but split the transaction into bounded commands under the Windows command-line limit: (1) exact preflight for candidate/dev supervisor/current Recovery Host identity; (2) packaged Install with immediate development rollback on nonzero exit; (3) core packaged manifest/status/adoption checks with rollback on any failure; (4) exact installed hashes and Scheduled Task principal/action/trigger checks with rollback on any failure. Current expected pre-transition Recovery Host is PID 19280 instance 5d13d8ac21067c251d8179f880629b1a and supervisor is development/healthy PID 7832. Do not reboot/logoff/restart runtime, edit repository source, commit, push, release, publish, or deploy.
- Objective revision: `4`
- Objective SHA-256: `17baec05017f113b240cbb705d255372b48480d2c9cd7784e455c032b0150634`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `a55a7afa723be43c5e6420521747de0d635c2b399cadceca78e139639dc35ff9`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 58826 | 2026-09-15T09:13:42.451Z | wave_replanned |  | PREFLIGHT | reason=Wave 39aac8e32ace4528928a59a8957c234d did not execute PowerShell because Windows rejected the single wrapper command line as too long. Split the unchanged safe transition into four shorter commands. Install command rolls back immediately on nonzero exit; each postcondition command rolls back to development mode before throwing on any invariant failure. This changes only the controller execution shape, not product source or transition semantics. |
| 58827 | 2026-09-15T09:13:42.863Z | observation_span_recorded |  |  |  |
| 58828 | 2026-09-15T09:13:48.599Z | observation_span_recorded |  |  |  |
| 58829 | 2026-09-15T09:13:49.015Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 58836 | 2026-09-15T09:14:29.725Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 58837 | 2026-09-15T09:14:29.956Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 58838 | 2026-09-15T09:14:30.149Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 58839 | 2026-09-15T09:14:30.341Z | state_transition | READY | ROUTED | reason=route_selected |
| 58840 | 2026-09-15T09:14:30.598Z | observation_span_recorded |  |  |  |
| 58841 | 2026-09-15T09:14:31.232Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=89bd719c198d432d96b9894e565f299d |
| 58842 | 2026-09-15T09:14:31.459Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 58843 | 2026-09-15T09:14:32.048Z | observation_span_recorded |  |  |  |
| 58844 | 2026-09-15T09:14:32.409Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=89bd719c198d432d96b9894e565f299d |
| 58845 | 2026-09-15T09:14:32.659Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 58846 | 2026-09-15T09:14:33.263Z | proof_cache_miss |  |  | reason=cold; stage_id=check:78683ed6d883f140; input_fingerprint=03f238e5025129ca98b3fe7af8d75a390a1f4a35e0e4ce851c26d28e08a7a2fd |
| 58847 | 2026-09-15T09:14:33.705Z | managed_process_admitted |  |  | owner=default |
| 58848 | 2026-09-15T09:14:34.130Z | managed_process_started |  |  | owner=default |
| 58849 | 2026-09-15T09:14:37.337Z | managed_process_terminal |  |  | owner=default |
| 58850 | 2026-09-15T09:14:37.759Z | proof_recorded |  |  | stage_id=check:78683ed6d883f140; status=passed; cache_hit=False; input_fingerprint=03f238e5025129ca98b3fe7af8d75a390a1f4a35e0e4ce851c26d28e08a7a2fd |
| 58851 | 2026-09-15T09:14:38.029Z | proof_cache_miss |  |  | reason=cold; stage_id=check:6f213afd4c45aa89; input_fingerprint=130ebdb08bc0de573af5fe7b57028bcd5982b4c7591969b0b28e3f739c7505ba |
| 58852 | 2026-09-15T09:14:38.506Z | managed_process_admitted |  |  | owner=default |
| 58853 | 2026-09-15T09:14:38.873Z | managed_process_started |  |  | owner=default |
| 58854 | 2026-09-15T09:15:04.704Z | managed_process_terminal |  |  | owner=default |
| 58855 | 2026-09-15T09:15:05.165Z | proof_recorded |  |  | stage_id=check:6f213afd4c45aa89; status=failed; cache_hit=False; input_fingerprint=130ebdb08bc0de573af5fe7b57028bcd5982b4c7591969b0b28e3f739c7505ba |
| 58856 | 2026-09-15T09:15:05.421Z | observation_span_recorded |  |  |  |
| 58857 | 2026-09-15T09:15:05.673Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 58858 | 2026-09-15T09:15:05.946Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 58859 | 2026-09-15T09:15:06.325Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 58869 | 2026-09-15T09:16:37.322Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:78683ed6d883f140 | passed | 03f238e5025129ca98b3fe7af8d75a390a1f4a35e0e4ce851c26d28e08a7a2fd | False | 4105 | 0 |
| check:6f213afd4c45aa89 | failed | 130ebdb08bc0de573af5fe7b57028bcd5982b4c7591969b0b28e3f739c7505ba | False | 26664 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `126`
- Chain head: `a1b6c357935ccb198a60f090f208d3c0dbec36c62138d7762fa8ed0a545815c5`
