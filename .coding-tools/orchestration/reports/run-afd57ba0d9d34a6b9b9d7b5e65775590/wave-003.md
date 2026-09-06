# Orchestration Wave 3

- Run: `afd57ba0d9d34a6b9b9d7b5e65775590`
- Wave: `6380d0a4c21246a6bb753bb3b12cb829`
- Objective: C5 material current-installer lifecycle on exact HEAD 9e752e34db745cd4fb2d0830a517910eced9c37f, linked to C5 contract checkpoint fd7c90d5d2db477cbc45e7bfa280d3fc and predecessor C4 checkpoint 777480e8957941f9ade53ec06e248d55. Use only C:\Users\Admin\AppData\Local\Temp\codex-web-c5-9e752e34 for test install/profile/evidence. Prove current 1.0.0 clean silent install, isolated recovery-host descriptor/process/loopback-listener health with autostart/tunnels disabled, exact isolated process cleanup, silent uninstall, and before/after production descriptor/scheduled-task/registry/legacy-shortcut invariants. Authenticated HTTP ping remains explicitly BLOCKED_BY_SERVER_POLICY and is not claimed. Do not run normal UI, C4 build/smoke/refresh, historical installer yet, publish/tag/release/deploy, or forbidden ACK.
- Objective revision: `3`
- Objective SHA-256: `bc3c10ed0dd0e0993d8280842452b2dcf67166c8969e394c4bb4a50756f12b6d`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `9e752e34db745cd4fb2d0830a517910eced9c37f`
- Worktree fingerprint: `6546f235f77e31e7b47a1f6c568d1f6291fec2c3fce76edc6b85030cc9b5259e`
- Contract fingerprint: `4d349d411b8887238ad4a1f9f43404a9bef00c6de368373ca6d72f1c271aea86`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 41620 | 2026-09-06T05:56:06.685Z | wave_replanned |  | PREFLIGHT | reason=CHECK_FAILED on Wave a154ccaf89ad4fdf968fda1a869b2d63 because Windows rejected the single lifecycle command before execution with 'The command line is too long.' A subsequent idempotency replay was blocked with outcome unknown; auxiliary read-only reconciliation then proved C5_ROOT_EXISTS=False, matching installer registry=0, current 1.0.0 shortcuts=False, C5 process count=0, and the production descriptor SHA256 remained d2705139ef748fa373576ee9ab78ac11c845e70dc076f459685ecf5b136a7faa. Split the frozen contract into five bounded sequential commands with temp evidence files. |
| 41621 | 2026-09-06T05:56:06.932Z | observation_span_recorded |  |  |  |
| 41624 | 2026-09-06T05:56:08.522Z | observation_span_recorded |  |  |  |
| 41625 | 2026-09-06T05:56:08.822Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 41627 | 2026-09-06T05:56:09.512Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 41629 | 2026-09-06T05:56:09.895Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 41630 | 2026-09-06T05:56:10.323Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 41631 | 2026-09-06T05:56:10.522Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 41632 | 2026-09-06T05:56:10.688Z | state_transition | READY | ROUTED | reason=route_selected |
| 41633 | 2026-09-06T05:56:10.874Z | observation_span_recorded |  |  |  |
| 41634 | 2026-09-06T05:56:11.913Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=8820785e7f194e6c8f842478b6c3a19c |
| 41635 | 2026-09-06T05:56:12.086Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 41636 | 2026-09-06T05:56:12.980Z | observation_span_recorded |  |  |  |
| 41637 | 2026-09-06T05:56:13.238Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=8820785e7f194e6c8f842478b6c3a19c |
| 41638 | 2026-09-06T05:56:13.380Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 41639 | 2026-09-06T05:56:14.184Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ea5dcc8a7286c856; input_fingerprint=532396489e9fd8d5fa0f25ee382be89fcd50605bf591ed0e27f99a4d6a6fd534 |
| 41640 | 2026-09-06T05:56:14.629Z | managed_process_admitted |  |  | owner=default |
| 41641 | 2026-09-06T05:56:14.936Z | managed_process_started |  |  | owner=default |
| 41645 | 2026-09-06T05:56:19.673Z | managed_process_terminal |  |  | owner=default |
| 41646 | 2026-09-06T05:56:20.098Z | proof_recorded |  |  | stage_id=check:ea5dcc8a7286c856; status=passed; cache_hit=False; input_fingerprint=532396489e9fd8d5fa0f25ee382be89fcd50605bf591ed0e27f99a4d6a6fd534 |
| 41647 | 2026-09-06T05:56:20.278Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b96b56af18404a26; input_fingerprint=55af11491553661ba668668d459bed565ab7b49782824212dd988fa832e64455 |
| 41648 | 2026-09-06T05:56:20.692Z | managed_process_admitted |  |  | owner=default |
| 41649 | 2026-09-06T05:56:21.014Z | managed_process_started |  |  | owner=default |
| 41650 | 2026-09-06T05:56:34.956Z | managed_process_terminal |  |  | owner=default |
| 41651 | 2026-09-06T05:56:35.590Z | proof_recorded |  |  | stage_id=check:b96b56af18404a26; status=failed; cache_hit=False; input_fingerprint=55af11491553661ba668668d459bed565ab7b49782824212dd988fa832e64455 |
| 41652 | 2026-09-06T05:56:35.926Z | observation_span_recorded |  |  |  |
| 41653 | 2026-09-06T05:56:36.273Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 41654 | 2026-09-06T05:56:36.533Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 41655 | 2026-09-06T05:56:36.805Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:ea5dcc8a7286c856 | passed | 532396489e9fd8d5fa0f25ee382be89fcd50605bf591ed0e27f99a4d6a6fd534 | False | 5530 | 0 |
| check:b96b56af18404a26 | failed | 55af11491553661ba668668d459bed565ab7b49782824212dd988fa832e64455 | False | 14852 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `114`
- Chain head: `5612743aa5665c91bcb01266569110632f1972baf496a720e10100a01c621dfe`
