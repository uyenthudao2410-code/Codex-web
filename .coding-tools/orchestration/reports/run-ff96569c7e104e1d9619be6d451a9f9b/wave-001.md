# Orchestration Wave 1

- Run: `ff96569c7e104e1d9619be6d451a9f9b`
- Wave: `f0fd684789f44d37a9f9e44bfede15e9`
- Objective: Fix the confirmed remaining live cross-tab projection leak on legacy/unscoped stateful MCP session aliases. HTTPSessionManager.get() currently maps unscoped legacy Mcp-Session-Id aliases to process-global Runtime/execution_context_id='', so different ChatWeb tabs can replace each other's task/run. Implement stable per-alias execution-scoped rebound: distinct raw legacy aliases -> distinct deterministic task/run scopes; same raw alias reconnect -> same task/run scope; server returns a canonical workspace-scoped session alias; legacy rebound must never adopt/mutate process-global task state. Preserve normal initialized ctx_ session semantics, no-session compatibility isolation, accepted MCP-2026 task_context_id behavior, accepted token accounting, and exactly 8 tools. Prefer transport_http.py plus test_workspace_session_isolation.py only. Prepare only; no mutation.
- Mode: `mcp_only`
- Base HEAD: `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc`
- Worktree fingerprint: `6c25b3bdf020629f1dfd643c49d7923c8d52d11b919bc7a1ab53793973c7f829`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21135 | 2026-08-19T09:08:48.043Z | run_started |  | PREFLIGHT |  |
| 21136 | 2026-08-19T09:08:48.820Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21137 | 2026-08-19T09:09:13.512Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21138 | 2026-08-19T09:09:26.501Z | solution_shadow_recommended |  |  |  |
| 21139 | 2026-08-19T09:09:37.566Z | managed_process_admitted |  |  | owner=default |
| 21140 | 2026-08-19T09:09:37.850Z | managed_process_started |  |  | owner=default |
| 21141 | 2026-08-19T09:09:38.260Z | managed_process_terminal |  |  | owner=default |
| 21142 | 2026-08-19T09:09:49.438Z | managed_process_admitted |  |  | owner=default |
| 21143 | 2026-08-19T09:09:49.715Z | managed_process_started |  |  | owner=default |
| 21144 | 2026-08-19T09:09:51.130Z | managed_process_terminal |  |  | owner=default |
| 21145 | 2026-08-19T09:10:20.097Z | managed_process_admitted |  |  | owner=default |
| 21146 | 2026-08-19T09:10:20.357Z | managed_process_started |  |  | owner=default |
| 21147 | 2026-08-19T09:10:20.716Z | managed_process_terminal |  |  | owner=default |
| 21148 | 2026-08-19T09:10:23.351Z | managed_process_admitted |  |  | owner=default |
| 21149 | 2026-08-19T09:10:23.598Z | managed_process_started |  |  | owner=default |
| 21150 | 2026-08-19T09:10:24.876Z | managed_process_terminal |  |  | owner=default |
| 21151 | 2026-08-19T09:10:34.404Z | managed_process_admitted |  |  | owner=default |
| 21152 | 2026-08-19T09:10:34.642Z | managed_process_started |  |  | owner=default |
| 21153 | 2026-08-19T09:10:36.088Z | managed_process_terminal |  |  | owner=default |
| 21154 | 2026-08-19T09:10:50.648Z | managed_process_admitted |  |  | owner=default |
| 21155 | 2026-08-19T09:10:50.894Z | managed_process_started |  |  | owner=default |
| 21156 | 2026-08-19T09:10:51.289Z | managed_process_terminal |  |  | owner=default |
| 21157 | 2026-08-19T09:11:03.803Z | managed_process_admitted |  |  | owner=default |
| 21158 | 2026-08-19T09:11:04.056Z | managed_process_started |  |  | owner=default |
| 21159 | 2026-08-19T09:11:04.458Z | managed_process_terminal |  |  | owner=default |
| 21160 | 2026-08-19T09:11:15.240Z | managed_process_admitted |  |  | owner=default |
| 21161 | 2026-08-19T09:11:15.456Z | managed_process_started |  |  | owner=default |
| 21162 | 2026-08-19T09:11:17.014Z | managed_process_terminal |  |  | owner=default |
| 21163 | 2026-08-19T09:11:42.985Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 21164 | 2026-08-19T09:11:43.148Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 21165 | 2026-08-19T09:11:43.289Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 21166 | 2026-08-19T09:11:43.434Z | state_transition | READY | ROUTED | reason=route_selected |
| 21167 | 2026-08-19T09:11:43.987Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4048996d4eaf45cfbf4d6443efaa0c95 |
| 21168 | 2026-08-19T09:11:44.138Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 21169 | 2026-08-19T09:11:44.572Z | patch_surface_observed |  |  |  |
| 21170 | 2026-08-19T09:11:44.801Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4048996d4eaf45cfbf4d6443efaa0c95 |
| 21171 | 2026-08-19T09:11:44.971Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 21172 | 2026-08-19T09:11:45.281Z | proof_cache_miss |  |  | reason=cold; stage_id=check:c8ee2cf0d73bb748; input_fingerprint=fc2d6b58bdef2749daea6ad4da08d827879382b301394f955591844b6a4069d5 |
| 21173 | 2026-08-19T09:11:45.636Z | managed_process_admitted |  |  | owner=default |
| 21174 | 2026-08-19T09:11:45.906Z | managed_process_started |  |  | owner=default |
| 21175 | 2026-08-19T09:11:46.373Z | managed_process_terminal |  |  | owner=default |
| 21176 | 2026-08-19T09:11:46.669Z | proof_recorded |  |  | stage_id=check:c8ee2cf0d73bb748; status=passed; cache_hit=False; input_fingerprint=fc2d6b58bdef2749daea6ad4da08d827879382b301394f955591844b6a4069d5 |
| 21177 | 2026-08-19T09:11:46.848Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:80a1a46bd01d26a3; input_fingerprint=28d38f3a3ee44fd817f5297871652529f316778e22913dea2404f9bb26283b22 |
| 21178 | 2026-08-19T09:11:47.135Z | managed_process_admitted |  |  | owner=default |
| 21179 | 2026-08-19T09:11:47.373Z | managed_process_started |  |  | owner=default |
| 21180 | 2026-08-19T09:11:47.766Z | managed_process_terminal |  |  | owner=default |
| 21181 | 2026-08-19T09:11:48.034Z | proof_recorded |  |  | stage_id=check:80a1a46bd01d26a3; status=passed; cache_hit=False; input_fingerprint=28d38f3a3ee44fd817f5297871652529f316778e22913dea2404f9bb26283b22 |
| 21182 | 2026-08-19T09:11:48.174Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b941de2adf2750bf; input_fingerprint=7590c513e5796b67c0216edadd3a00480cf3ef77caa494b6b72aabd58aef936b |
| 21183 | 2026-08-19T09:11:48.524Z | managed_process_admitted |  |  | owner=default |
| 21184 | 2026-08-19T09:11:48.773Z | managed_process_started |  |  | owner=default |
| 21185 | 2026-08-19T09:11:49.156Z | managed_process_terminal |  |  | owner=default |
| 21186 | 2026-08-19T09:11:49.490Z | proof_recorded |  |  | stage_id=check:b941de2adf2750bf; status=passed; cache_hit=False; input_fingerprint=7590c513e5796b67c0216edadd3a00480cf3ef77caa494b6b72aabd58aef936b |
| 21187 | 2026-08-19T09:11:49.650Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=268dea88d8dc885e20d44ef8be831e97f98c0dabe32a8d9a713b2bc6c7eb8f45 |
| 21188 | 2026-08-19T09:11:49.950Z | managed_process_admitted |  |  | owner=default |
| 21189 | 2026-08-19T09:11:50.205Z | managed_process_started |  |  | owner=default |
| 21190 | 2026-08-19T09:12:07.372Z | managed_process_admitted |  |  | owner=default |
| 21191 | 2026-08-19T09:12:07.622Z | managed_process_started |  |  | owner=default |
| 21192 | 2026-08-19T09:12:08.041Z | managed_process_terminal |  |  | owner=default |
| 21193 | 2026-08-19T09:12:08.470Z | managed_process_terminal |  |  | owner=default |
| 21194 | 2026-08-19T09:12:08.816Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=268dea88d8dc885e20d44ef8be831e97f98c0dabe32a8d9a713b2bc6c7eb8f45 |
| 21195 | 2026-08-19T09:12:09.066Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 21196 | 2026-08-19T09:12:09.221Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 21197 | 2026-08-19T09:12:09.512Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 21198 | 2026-08-19T09:13:46.374Z | state_transition | REPLAN | ABORTED | reason=task_stopped |
| 21199 | 2026-08-19T09:13:46.694Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:c8ee2cf0d73bb748 | passed | fc2d6b58bdef2749daea6ad4da08d827879382b301394f955591844b6a4069d5 | False | 1080 | 0 |
| check:80a1a46bd01d26a3 | passed | 28d38f3a3ee44fd817f5297871652529f316778e22913dea2404f9bb26283b22 | False | 910 | 0 |
| check:b941de2adf2750bf | passed | 7590c513e5796b67c0216edadd3a00480cf3ef77caa494b6b72aabd58aef936b | False | 974 | 0 |
| verify:tests | failed | 268dea88d8dc885e20d44ef8be831e97f98c0dabe32a8d9a713b2bc6c7eb8f45 | False | 18859 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `65`
- Chain head: `0fa400bc2a39e64ca163309f6a4353e9e2a198a6eb361516672b8c4f20ce9a43`
