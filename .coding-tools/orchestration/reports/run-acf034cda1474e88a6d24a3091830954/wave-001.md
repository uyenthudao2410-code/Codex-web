# Orchestration Wave 1

- Run: `acf034cda1474e88a6d24a3091830954`
- Wave: `64bf2fa8cc9545a5ae0aa4fa26d17265`
- Objective: Run a pre-checkpoint source acceptance battery over the accumulated P4 validator, control-plane ACK compatibility, benchmark harness, dormant P5 treatment planner, and P5 measurement implementation. This is verification only: do not change source, readiness thresholds, treatment state, or promotion policy. Require raw research stress clean, multilayer normal+strict clean, focused Python regressions clean, diff hygiene clean, and packaging/build smoke clean. Do not commit, push, restart, deploy, or activate treatment in this wave.
- Mode: `mcp_only`
- Base HEAD: `4aa8a99b877f20b5f2f4bb2ce50e0cbc477a25d2`
- Worktree fingerprint: `57a3d5acb5e1b4f6381c3ff61c08733aa0c9fc410bd79ee9bb7c5def98d7e96b`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 22584 | 2026-08-20T04:33:26.726Z | run_started |  | PREFLIGHT |  |
| 22585 | 2026-08-20T04:33:27.233Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 22586 | 2026-08-20T04:33:27.671Z | managed_process_admitted |  |  | owner=default |
| 22587 | 2026-08-20T04:33:27.972Z | managed_process_started |  |  | owner=default |
| 22588 | 2026-08-20T04:35:06.167Z | managed_process_terminal |  |  | owner=default |
| 22589 | 2026-08-20T04:35:06.326Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 22590 | 2026-08-20T04:35:06.456Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 22591 | 2026-08-20T04:35:06.581Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 22592 | 2026-08-20T04:35:06.739Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 22593 | 2026-08-20T04:35:06.907Z | state_transition | READY | ROUTED | reason=route_selected |
| 22594 | 2026-08-20T04:35:07.356Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=36fea922a8444a9b9eb7f5d8cd8421c9 |
| 22595 | 2026-08-20T04:35:07.496Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 22596 | 2026-08-20T04:35:08.010Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=36fea922a8444a9b9eb7f5d8cd8421c9 |
| 22597 | 2026-08-20T04:35:08.162Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 22598 | 2026-08-20T04:35:08.566Z | proof_cache_miss |  |  | reason=cold; stage_id=check:4814bb8b841368f8; input_fingerprint=b63ca7c6e3bd0a10715f097e8b46fc88344cad7021ceab1e2a3b8244e352b149 |
| 22599 | 2026-08-20T04:35:09.066Z | managed_process_admitted |  |  | owner=default |
| 22600 | 2026-08-20T04:35:09.366Z | managed_process_started |  |  | owner=default |
| 22601 | 2026-08-20T04:35:46.045Z | managed_process_terminal |  |  | owner=default |
| 22602 | 2026-08-20T04:35:46.421Z | proof_recorded |  |  | stage_id=check:4814bb8b841368f8; status=passed; cache_hit=False; input_fingerprint=b63ca7c6e3bd0a10715f097e8b46fc88344cad7021ceab1e2a3b8244e352b149 |
| 22603 | 2026-08-20T04:35:46.568Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:fd71cdc4b22e7c92; input_fingerprint=612b58166459f735905dc04a55e2e357bfe112546aa324c6e1809c4f7e6a1c00 |
| 22604 | 2026-08-20T04:35:46.994Z | managed_process_admitted |  |  | owner=default |
| 22605 | 2026-08-20T04:35:47.238Z | managed_process_started |  |  | owner=default |
| 22606 | 2026-08-20T04:36:12.438Z | managed_process_terminal |  |  | owner=default |
| 22607 | 2026-08-20T04:36:12.804Z | proof_recorded |  |  | stage_id=check:fd71cdc4b22e7c92; status=passed; cache_hit=False; input_fingerprint=612b58166459f735905dc04a55e2e357bfe112546aa324c6e1809c4f7e6a1c00 |
| 22608 | 2026-08-20T04:36:12.956Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:4b1598eb83d27135; input_fingerprint=6069087ef02f9020a1218a48fe9e13675c7bc8ab3f4d352c6e5e4f4ebe823de4 |
| 22609 | 2026-08-20T04:36:13.314Z | managed_process_admitted |  |  | owner=default |
| 22610 | 2026-08-20T04:36:13.544Z | managed_process_started |  |  | owner=default |
| 22611 | 2026-08-20T04:36:45.523Z | managed_process_terminal |  |  | owner=default |
| 22612 | 2026-08-20T04:36:45.863Z | proof_recorded |  |  | stage_id=check:4b1598eb83d27135; status=passed; cache_hit=False; input_fingerprint=6069087ef02f9020a1218a48fe9e13675c7bc8ab3f4d352c6e5e4f4ebe823de4 |
| 22613 | 2026-08-20T04:36:46.023Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:9647a5d1f13b481d; input_fingerprint=71196a349f5ff6c74fc7e05aa76677a4ae69dc1da90214040eb8137b3482d086 |
| 22614 | 2026-08-20T04:36:46.333Z | managed_process_admitted |  |  | owner=default |
| 22615 | 2026-08-20T04:36:46.657Z | managed_process_started |  |  | owner=default |
| 22616 | 2026-08-20T04:37:18.992Z | managed_process_terminal |  |  | owner=default |
| 22617 | 2026-08-20T04:37:19.405Z | proof_recorded |  |  | stage_id=check:9647a5d1f13b481d; status=passed; cache_hit=False; input_fingerprint=71196a349f5ff6c74fc7e05aa76677a4ae69dc1da90214040eb8137b3482d086 |
| 22618 | 2026-08-20T04:37:19.622Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:44f99eab9c3cb541; input_fingerprint=3004205155f2a87ac541f6c51482e72a350aa148fd75e66c11bd899f5de167a0 |
| 22619 | 2026-08-20T04:37:19.954Z | managed_process_admitted |  |  | owner=default |
| 22620 | 2026-08-20T04:37:20.203Z | managed_process_started |  |  | owner=default |
| 22621 | 2026-08-20T04:37:34.871Z | managed_process_terminal |  |  | owner=default |
| 22622 | 2026-08-20T04:37:35.212Z | proof_recorded |  |  | stage_id=check:44f99eab9c3cb541; status=passed; cache_hit=False; input_fingerprint=3004205155f2a87ac541f6c51482e72a350aa148fd75e66c11bd899f5de167a0 |
| 22623 | 2026-08-20T04:37:35.402Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=db727c91bb5998c2d646017fdcc4a9a8dd971c1ce1ade5c13bd65738df354dbc |
| 22624 | 2026-08-20T04:37:35.806Z | managed_process_admitted |  |  | owner=default |
| 22625 | 2026-08-20T04:37:36.127Z | managed_process_started |  |  | owner=default |
| 22626 | 2026-08-20T04:37:36.991Z | managed_process_terminal |  |  | owner=default |
| 22627 | 2026-08-20T04:37:37.382Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=db727c91bb5998c2d646017fdcc4a9a8dd971c1ce1ade5c13bd65738df354dbc |
| 22628 | 2026-08-20T04:37:37.531Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:all; input_fingerprint=852f7b6e38098db13e47a55c058c59aba37ac2cbba600f0e48f778a694f03317 |
| 22629 | 2026-08-20T04:37:37.841Z | managed_process_admitted |  |  | owner=default |
| 22630 | 2026-08-20T04:37:38.111Z | managed_process_started |  |  | owner=default |
| 22631 | 2026-08-20T04:37:59.285Z | managed_process_terminal |  |  | owner=default |
| 22632 | 2026-08-20T04:37:59.651Z | proof_recorded |  |  | stage_id=verify:all; status=failed; cache_hit=False; input_fingerprint=852f7b6e38098db13e47a55c058c59aba37ac2cbba600f0e48f778a694f03317 |
| 22633 | 2026-08-20T04:37:59.841Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 22634 | 2026-08-20T04:38:00.006Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 22635 | 2026-08-20T04:38:00.181Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:4814bb8b841368f8 | passed | b63ca7c6e3bd0a10715f097e8b46fc88344cad7021ceab1e2a3b8244e352b149 | False | 37426 | 0 |
| check:fd71cdc4b22e7c92 | passed | 612b58166459f735905dc04a55e2e357bfe112546aa324c6e1809c4f7e6a1c00 | False | 25879 | 0 |
| check:4b1598eb83d27135 | passed | 6069087ef02f9020a1218a48fe9e13675c7bc8ab3f4d352c6e5e4f4ebe823de4 | False | 32581 | 0 |
| check:9647a5d1f13b481d | passed | 71196a349f5ff6c74fc7e05aa76677a4ae69dc1da90214040eb8137b3482d086 | False | 33067 | 0 |
| check:44f99eab9c3cb541 | passed | 3004205155f2a87ac541f6c51482e72a350aa148fd75e66c11bd899f5de167a0 | False | 15246 | 0 |
| check:466c2f308b48c766 | passed | db727c91bb5998c2d646017fdcc4a9a8dd971c1ce1ade5c13bd65738df354dbc | False | 1553 | 0 |
| verify:all | failed | 852f7b6e38098db13e47a55c058c59aba37ac2cbba600f0e48f778a694f03317 | False | 21765 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `70`
- Chain head: `eec6b2925d7779732fd55ac1886fa4116e120be9cac89604c6123c7e62e64a99`
