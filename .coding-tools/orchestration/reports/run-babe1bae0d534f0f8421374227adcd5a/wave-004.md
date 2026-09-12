# Orchestration Wave 4

- Run: `babe1bae0d534f0f8421374227adcd5a`
- Wave: `6f97b7af8d3d4d128606a056be94bbdb`
- Objective: Fix the activation restart preflight self-block so an explicitly authorized controlled restart can proceed when the only lifecycle_live_owned evidence is the exact current ChatWeb controller lease for this quiescent RUN. Keep global lifecycle classification unchanged and preserve all foreign/other ownership barriers. Add focused regression coverage for exact self lease allowed and foreign/additional/unsafe ownership still blocked.
- Objective revision: `3`
- Objective SHA-256: `5a91a48b8b4e3d94a46de2932ae3b5dfca2b3bf8d14783f6aa2810fdcc29a979`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `23af0945846828974bfb9d0bc6254867ead417bc07c9d73e1a78b7e4b997ffc3`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 49848 | 2026-09-11T16:01:06.933Z | wave_replanned |  | PREFLIGHT | reason=Changed evidence and scope: the live controlled-restart wave cannot proceed because activation preflight counts the exact calling ChatWeb controller lease as lifecycle_live_owned even though this task was paused/waiting and managed execution is quiescent. Replan the SAME RUN to implement a bounded self-controller preflight discount only for the exact current caller/current RUN when that controller lease is the sole otherwise-live ownership source. Do not change global LIVE_OWNED classification. Foreign controller leases, extra ownership, write fences, managed jobs, background operations, agent lanes, ACCEPTING work, ambiguous identity, or non-quiescent state must still block fail-closed. Preserve unrelated dirty bytes. After focused tests, return to live controlled-restart proof; do not claim full Problem resolution from unit tests. |
| 49849 | 2026-09-11T16:01:07.258Z | observation_span_recorded |  |  |  |
| 49850 | 2026-09-11T16:01:24.792Z | observation_span_recorded |  |  |  |
| 49851 | 2026-09-11T16:01:25.008Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 49852 | 2026-09-11T16:01:55.394Z | managed_process_admitted |  |  | owner=default |
| 49853 | 2026-09-11T16:01:55.800Z | managed_process_started |  |  | owner=default |
| 49854 | 2026-09-11T16:01:56.343Z | managed_process_terminal |  |  | owner=default |
| 49855 | 2026-09-11T16:03:08.035Z | managed_process_admitted |  |  | owner=default |
| 49856 | 2026-09-11T16:03:08.410Z | managed_process_started |  |  | owner=default |
| 49857 | 2026-09-11T16:03:08.878Z | managed_process_terminal |  |  | owner=default |
| 49858 | 2026-09-11T16:03:21.044Z | managed_process_admitted |  |  | owner=default |
| 49859 | 2026-09-11T16:03:21.702Z | managed_process_started |  |  | owner=default |
| 49860 | 2026-09-11T16:03:22.293Z | managed_process_terminal |  |  | owner=default |
| 49861 | 2026-09-11T16:03:29.202Z | managed_process_admitted |  |  | owner=default |
| 49862 | 2026-09-11T16:03:29.527Z | managed_process_started |  |  | owner=default |
| 49863 | 2026-09-11T16:03:30.051Z | managed_process_terminal |  |  | owner=default |
| 49864 | 2026-09-11T16:03:36.686Z | managed_process_admitted |  |  | owner=default |
| 49865 | 2026-09-11T16:03:37.095Z | managed_process_started |  |  | owner=default |
| 49866 | 2026-09-11T16:03:37.627Z | managed_process_terminal |  |  | owner=default |
| 49867 | 2026-09-11T16:03:49.326Z | managed_process_admitted |  |  | owner=default |
| 49868 | 2026-09-11T16:03:49.727Z | managed_process_started |  |  | owner=default |
| 49869 | 2026-09-11T16:03:50.263Z | managed_process_terminal |  |  | owner=default |
| 49870 | 2026-09-11T16:03:58.695Z | managed_process_admitted |  |  | owner=default |
| 49871 | 2026-09-11T16:03:59.035Z | managed_process_started |  |  | owner=default |
| 49872 | 2026-09-11T16:03:59.461Z | managed_process_terminal |  |  | owner=default |
| 49873 | 2026-09-11T16:04:10.319Z | managed_process_admitted |  |  | owner=default |
| 49874 | 2026-09-11T16:04:11.003Z | managed_process_started |  |  | owner=default |
| 49875 | 2026-09-11T16:04:11.585Z | managed_process_terminal |  |  | owner=default |
| 49876 | 2026-09-11T16:04:21.318Z | managed_process_admitted |  |  | owner=default |
| 49877 | 2026-09-11T16:04:21.707Z | managed_process_started |  |  | owner=default |
| 49878 | 2026-09-11T16:04:22.235Z | managed_process_terminal |  |  | owner=default |
| 49879 | 2026-09-11T16:04:28.811Z | managed_process_admitted |  |  | owner=default |
| 49880 | 2026-09-11T16:04:29.252Z | managed_process_started |  |  | owner=default |
| 49881 | 2026-09-11T16:04:29.802Z | managed_process_terminal |  |  | owner=default |
| 49882 | 2026-09-11T16:04:37.960Z | managed_process_admitted |  |  | owner=default |
| 49883 | 2026-09-11T16:04:38.301Z | managed_process_started |  |  | owner=default |
| 49884 | 2026-09-11T16:04:38.819Z | managed_process_terminal |  |  | owner=default |
| 49885 | 2026-09-11T16:04:47.793Z | managed_process_admitted |  |  | owner=default |
| 49886 | 2026-09-11T16:04:48.203Z | managed_process_started |  |  | owner=default |
| 49887 | 2026-09-11T16:04:48.777Z | managed_process_terminal |  |  | owner=default |
| 49888 | 2026-09-11T16:05:28.711Z | managed_process_admitted |  |  | owner=default |
| 49889 | 2026-09-11T16:05:29.138Z | managed_process_started |  |  | owner=default |
| 49890 | 2026-09-11T16:05:29.675Z | managed_process_terminal |  |  | owner=default |
| 49891 | 2026-09-11T16:05:36.186Z | managed_process_admitted |  |  | owner=default |
| 49892 | 2026-09-11T16:05:36.587Z | managed_process_started |  |  | owner=default |
| 49893 | 2026-09-11T16:05:37.069Z | managed_process_terminal |  |  | owner=default |
| 49894 | 2026-09-11T16:05:43.436Z | managed_process_admitted |  |  | owner=default |
| 49895 | 2026-09-11T16:05:43.886Z | managed_process_started |  |  | owner=default |
| 49896 | 2026-09-11T16:05:44.420Z | managed_process_terminal |  |  | owner=default |
| 49897 | 2026-09-11T16:06:08.594Z | managed_process_admitted |  |  | owner=default |
| 49898 | 2026-09-11T16:06:09.052Z | managed_process_started |  |  | owner=default |
| 49899 | 2026-09-11T16:06:09.612Z | managed_process_terminal |  |  | owner=default |
| 49900 | 2026-09-11T16:06:40.119Z | managed_process_admitted |  |  | owner=default |
| 49901 | 2026-09-11T16:06:40.460Z | managed_process_started |  |  | owner=default |
| 49902 | 2026-09-11T16:06:40.978Z | managed_process_terminal |  |  | owner=default |
| 49903 | 2026-09-11T16:07:20.077Z | managed_process_admitted |  |  | owner=default |
| 49904 | 2026-09-11T16:07:20.452Z | managed_process_started |  |  | owner=default |
| 49905 | 2026-09-11T16:07:20.969Z | managed_process_terminal |  |  | owner=default |
| 49906 | 2026-09-11T16:08:36.826Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 49907 | 2026-09-11T16:08:37.140Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 49908 | 2026-09-11T16:08:37.420Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 49909 | 2026-09-11T16:08:37.585Z | state_transition | READY | ROUTED | reason=route_selected |
| 49910 | 2026-09-11T16:08:37.869Z | observation_span_recorded |  |  |  |
| 49911 | 2026-09-11T16:08:38.799Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=788bff5c7e8d48b88b60b74adc99f4a0 |
| 49912 | 2026-09-11T16:08:39.058Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 49913 | 2026-09-11T16:08:40.021Z | patch_surface_observed |  |  |  |
| 49914 | 2026-09-11T16:08:40.251Z | observation_span_recorded |  |  |  |
| 49915 | 2026-09-11T16:08:40.564Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=788bff5c7e8d48b88b60b74adc99f4a0 |
| 49916 | 2026-09-11T16:08:40.741Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 49917 | 2026-09-11T16:08:41.633Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=62dfdd2e5573fc500d5b9beaed20fc3989111ed38dac45d4bd3f0135e5f89548 |
| 49918 | 2026-09-11T16:08:42.152Z | managed_process_admitted |  |  | owner=default |
| 49919 | 2026-09-11T16:08:42.561Z | managed_process_started |  |  | owner=default |
| 49920 | 2026-09-11T16:08:43.777Z | managed_process_terminal |  |  | owner=default |
| 49921 | 2026-09-11T16:08:44.086Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=62dfdd2e5573fc500d5b9beaed20fc3989111ed38dac45d4bd3f0135e5f89548 |
| 49922 | 2026-09-11T16:08:44.303Z | observation_span_recorded |  |  |  |
| 49923 | 2026-09-11T16:08:44.547Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 49924 | 2026-09-11T16:08:44.760Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 49925 | 2026-09-11T16:08:44.970Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 62dfdd2e5573fc500d5b9beaed20fc3989111ed38dac45d4bd3f0135e5f89548 | False | 2062 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `326`
- Chain head: `0ec6738f6d548fe6b72ddcbf21169e5517df57d43a6a365e26b7e46224cd43c8`
