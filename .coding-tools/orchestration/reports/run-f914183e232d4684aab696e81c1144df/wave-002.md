# Orchestration Wave 2

- Run: `f914183e232d4684aab696e81c1144df`
- Wave: `bc912bc9217a4526ac1aca127b1164d1`
- Objective: Implement the non-overlapping post-P4-MX completion wave only. Protected paths that must not be modified: electron/main.js, electron/panelPreload.js, resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py, resources/coding-tools-mcp/tests/test_execution_hub.py, tests/control-panel.test.js. Read and localize existing P4-MX runner/catalog/tests, P4 solution_economics/rework_diagnosis/readiness tests, paired_policy_evaluation/evaluation report APIs, package scripts and routing/P5 regression tests. Design the smallest additive patch for: (1) immutable evaluator-owned P4-MX manifest + deterministic human summary/replay verification from final report and manifest, (2) shared high-confidence durable replan reason classification and coverage diagnostics with ambiguous generic build/check failures left unclassified and no readiness threshold changes, (3) standalone orchestration_tax research report built only from canonical paired_policy_evaluation accepted pair IDs and accepted_result_evaluation, preserving unknown-not-zero and no automatic activation, (4) regression guards P5 dormant and auto deterministic/nonpromoting. Do not write yet.
- Mode: `mcp_only`
- Base HEAD: `66c2d17b68969c3a413b867cc7281f80fbaf4b45`
- Worktree fingerprint: `7698fdcfebe7afe093b8faddc04f674fb79832605a0e04297fbd136ccde15eea`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 23629 | 2026-08-20T10:21:27.659Z | wave_replanned |  | PREFLIGHT | reason=The prior run fingerprint predates the now-final-accepted post-P4-MX implementation and subsequent read-only evidence commands. This is a changed evidence-only strategy: use the authorized Git object database at exact eval commit 522dede8... instead of the security-blocked external worktree path, with no source mutation and temporary private-oracle material deleted within the same wave. |
| 23630 | 2026-08-20T10:21:28.504Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 23631 | 2026-08-20T10:23:55.997Z | managed_process_admitted |  |  | owner=chatweb |
| 23632 | 2026-08-20T10:23:56.347Z | managed_process_started |  |  | owner=chatweb |
| 23633 | 2026-08-20T10:23:56.811Z | managed_process_terminal |  |  | owner=chatweb |
| 23634 | 2026-08-20T10:24:07.630Z | managed_process_admitted |  |  | owner=chatweb |
| 23635 | 2026-08-20T10:24:07.938Z | managed_process_started |  |  | owner=chatweb |
| 23636 | 2026-08-20T10:24:22.373Z | managed_process_terminal |  |  | owner=chatweb |
| 23637 | 2026-08-20T10:24:34.461Z | managed_process_admitted |  |  | owner=chatweb |
| 23638 | 2026-08-20T10:24:34.713Z | managed_process_started |  |  | owner=chatweb |
| 23639 | 2026-08-20T10:24:35.105Z | managed_process_terminal |  |  | owner=chatweb |
| 23640 | 2026-08-20T10:24:54.892Z | managed_process_admitted |  |  | owner=chatweb |
| 23641 | 2026-08-20T10:24:55.221Z | managed_process_started |  |  | owner=chatweb |
| 23642 | 2026-08-20T10:24:56.139Z | managed_process_terminal |  |  | owner=chatweb |
| 23643 | 2026-08-20T10:25:05.681Z | managed_process_admitted |  |  | owner=chatweb |
| 23644 | 2026-08-20T10:25:05.988Z | managed_process_started |  |  | owner=chatweb |
| 23645 | 2026-08-20T10:25:06.394Z | managed_process_terminal |  |  | owner=chatweb |
| 23646 | 2026-08-20T10:25:17.491Z | managed_process_admitted |  |  | owner=chatweb |
| 23647 | 2026-08-20T10:25:17.838Z | managed_process_started |  |  | owner=chatweb |
| 23648 | 2026-08-20T10:25:18.282Z | managed_process_terminal |  |  | owner=chatweb |
| 23649 | 2026-08-20T10:25:27.848Z | managed_process_admitted |  |  | owner=chatweb |
| 23650 | 2026-08-20T10:25:28.155Z | managed_process_started |  |  | owner=chatweb |
| 23651 | 2026-08-20T10:25:28.563Z | managed_process_terminal |  |  | owner=chatweb |
| 23652 | 2026-08-20T10:25:39.738Z | managed_process_admitted |  |  | owner=chatweb |
| 23653 | 2026-08-20T10:25:40.089Z | managed_process_started |  |  | owner=chatweb |
| 23654 | 2026-08-20T10:25:40.445Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=chatweb |
| 23655 | 2026-08-20T10:25:50.289Z | managed_process_admitted |  |  | owner=chatweb |
| 23656 | 2026-08-20T10:25:50.597Z | managed_process_started |  |  | owner=chatweb |
| 23657 | 2026-08-20T10:25:50.975Z | managed_process_terminal |  |  | owner=chatweb |
| 23658 | 2026-08-20T10:26:02.666Z | managed_process_admitted |  |  | owner=chatweb |
| 23659 | 2026-08-20T10:26:02.964Z | managed_process_started |  |  | owner=chatweb |
| 23660 | 2026-08-20T10:26:03.408Z | managed_process_terminal |  |  | owner=chatweb |
| 23661 | 2026-08-20T10:26:17.991Z | managed_process_admitted |  |  | owner=chatweb |
| 23662 | 2026-08-20T10:26:18.304Z | managed_process_started |  |  | owner=chatweb |
| 23663 | 2026-08-20T10:26:18.742Z | managed_process_terminal |  |  | owner=chatweb |
| 23664 | 2026-08-20T10:26:40.418Z | managed_process_admitted |  |  | owner=chatweb |
| 23665 | 2026-08-20T10:26:40.718Z | managed_process_started |  |  | owner=chatweb |
| 23666 | 2026-08-20T10:26:41.160Z | managed_process_terminal |  |  | owner=chatweb |
| 23667 | 2026-08-20T10:26:48.956Z | managed_process_admitted |  |  | owner=chatweb |
| 23668 | 2026-08-20T10:26:49.263Z | managed_process_started |  |  | owner=chatweb |
| 23669 | 2026-08-20T10:26:49.738Z | managed_process_terminal |  |  | owner=chatweb |
| 23670 | 2026-08-20T10:27:06.691Z | managed_process_admitted |  |  | owner=chatweb |
| 23671 | 2026-08-20T10:27:07.038Z | managed_process_started |  |  | owner=chatweb |
| 23672 | 2026-08-20T10:27:09.569Z | managed_process_terminal |  |  | owner=chatweb |
| 23673 | 2026-08-20T10:27:22.455Z | managed_process_admitted |  |  | owner=chatweb |
| 23674 | 2026-08-20T10:27:24.466Z | managed_process_started |  |  | owner=chatweb |
| 23675 | 2026-08-20T10:27:25.029Z | managed_process_terminal |  |  | owner=chatweb |
| 23676 | 2026-08-20T10:27:34.873Z | managed_process_admitted |  |  | owner=chatweb |
| 23677 | 2026-08-20T10:27:35.280Z | managed_process_started |  |  | owner=chatweb |
| 23678 | 2026-08-20T10:27:35.691Z | managed_process_terminal |  |  | owner=chatweb |
| 23679 | 2026-08-20T10:27:47.626Z | managed_process_admitted |  |  | owner=chatweb |
| 23680 | 2026-08-20T10:27:47.878Z | managed_process_started |  |  | owner=chatweb |
| 23681 | 2026-08-20T10:27:49.005Z | managed_process_terminal |  |  | owner=chatweb |
| 23705 | 2026-08-20T10:38:00.239Z | managed_process_admitted |  |  | owner=chatweb |
| 23706 | 2026-08-20T10:38:00.523Z | managed_process_started |  |  | owner=chatweb |
| 23707 | 2026-08-20T10:38:01.128Z | managed_process_terminal |  |  | owner=chatweb |
| 23708 | 2026-08-20T10:41:55.422Z | managed_process_admitted |  |  | owner=chatweb |
| 23709 | 2026-08-20T10:41:55.705Z | managed_process_started |  |  | owner=chatweb |
| 23710 | 2026-08-20T10:41:56.197Z | managed_process_terminal |  |  | owner=chatweb |
| 23711 | 2026-08-20T10:42:01.697Z | managed_process_admitted |  |  | owner=chatweb |
| 23712 | 2026-08-20T10:42:01.998Z | managed_process_started |  |  | owner=chatweb |
| 23713 | 2026-08-20T10:42:02.397Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=chatweb |
| 23714 | 2026-08-20T10:42:16.523Z | managed_process_admitted |  |  | owner=chatweb |
| 23715 | 2026-08-20T10:42:16.855Z | managed_process_started |  |  | owner=chatweb |
| 23716 | 2026-08-20T10:42:18.605Z | managed_process_terminal |  |  | owner=chatweb |
| 23717 | 2026-08-20T10:42:24.111Z | managed_process_admitted |  |  | owner=chatweb |
| 23718 | 2026-08-20T10:42:24.379Z | managed_process_started |  |  | owner=chatweb |
| 23719 | 2026-08-20T10:42:24.738Z | managed_process_terminal |  |  | owner=chatweb |
| 23720 | 2026-08-20T10:42:33.055Z | managed_process_admitted |  |  | owner=chatweb |
| 23721 | 2026-08-20T10:42:33.381Z | managed_process_started |  |  | owner=chatweb |
| 23722 | 2026-08-20T10:42:33.905Z | managed_process_terminal |  |  | owner=chatweb |
| 23723 | 2026-08-20T10:44:20.807Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 23724 | 2026-08-20T10:44:38.116Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 23725 | 2026-08-20T10:47:48.874Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 23726 | 2026-08-20T10:48:04.127Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 23727 | 2026-08-20T10:48:04.286Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 23728 | 2026-08-20T10:48:04.494Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 23729 | 2026-08-20T10:48:04.658Z | state_transition | READY | ROUTED | reason=route_selected |
| 23730 | 2026-08-20T10:48:05.109Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=cfd5c7ec58194f859fdd027ee74a9559 |
| 23731 | 2026-08-20T10:48:05.345Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 23732 | 2026-08-20T10:48:05.817Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=cfd5c7ec58194f859fdd027ee74a9559 |
| 23733 | 2026-08-20T10:48:05.982Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 23734 | 2026-08-20T10:48:06.420Z | proof_cache_miss |  |  | reason=cold; stage_id=check:195fe463ccd2bc75; input_fingerprint=6c35e5c67179006211c1059eb7802e23456f2c61506d19fab960bb03390370af |
| 23735 | 2026-08-20T10:48:06.797Z | managed_process_admitted |  |  | owner=default |
| 23736 | 2026-08-20T10:48:07.072Z | managed_process_started |  |  | owner=default |
| 23737 | 2026-08-20T10:48:09.539Z | managed_process_terminal |  |  | owner=default |
| 23738 | 2026-08-20T10:48:09.827Z | proof_recorded |  |  | stage_id=check:195fe463ccd2bc75; status=failed; cache_hit=False; input_fingerprint=6c35e5c67179006211c1059eb7802e23456f2c61506d19fab960bb03390370af |
| 23739 | 2026-08-20T10:48:10.036Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 23740 | 2026-08-20T10:48:10.215Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 23741 | 2026-08-20T10:48:10.473Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:195fe463ccd2bc75 | failed | 6c35e5c67179006211c1059eb7802e23456f2c61506d19fab960bb03390370af | False | 3080 | 2 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `131`
- Chain head: `2a66c1bbe481126cf8998bbe329ef885e122340b471d36caa78b1a593e293561`
