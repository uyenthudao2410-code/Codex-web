# Orchestration Wave 1

- Run: `d05ba610174844eb831af8f23a3395d0`
- Wave: `0337a944db5e48aca8238be15435e7e5`
- Objective: Fix the genuine exact-fit tracked-diff byte-budget bug in crates/webcodex-workspace/src/project_context.rs. Current worktree_sha256 marks worktree partial whenever remaining becomes zero after bounded_git_output, even when a repository with HEAD has a single complete git diff whose byte length exactly equals max_tracked_diff_bytes. Preserve fail-closed partial classification when output actually truncates/exceeds the budget and when another required diff slice cannot be read. Add the smallest same-module unit regression proving an exact-fit complete HEAD diff remains complete, while existing large_tracked_diff_is_partial_instead_of_read_without_limit continues covering true overflow. Do not touch unrelated files, do not commit/push, do not restart, and do not manufacture a replan. This is a genuine representative P4 bugfix sample.
- Mode: `mcp_only`
- Base HEAD: `b7af2598297870e816dd131b0f73e0f77d7608d5`
- Worktree fingerprint: `a75e8f98c4f459be87d8bfb27a9b55e03ac49336337aefe70b016487a60b680b`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 18057 | 2026-08-18T15:43:10.862Z | run_started |  | PREFLIGHT |  |
| 18058 | 2026-08-18T15:43:15.960Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 18059 | 2026-08-18T15:44:21.075Z | solution_shadow_recommended |  |  |  |
| 18060 | 2026-08-18T15:44:46.661Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 18061 | 2026-08-18T15:44:46.760Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 18062 | 2026-08-18T15:44:46.861Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 18063 | 2026-08-18T15:44:46.967Z | state_transition | READY | ROUTED | reason=route_selected |
| 18064 | 2026-08-18T15:44:47.393Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=bc46eed33f154dfd9f0a4cdb49833c50 |
| 18065 | 2026-08-18T15:44:47.518Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 18066 | 2026-08-18T15:44:47.862Z | solution_shadow_patch_surface_observed |  |  |  |
| 18067 | 2026-08-18T15:44:48.113Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=bc46eed33f154dfd9f0a4cdb49833c50 |
| 18068 | 2026-08-18T15:44:48.228Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 18069 | 2026-08-18T15:44:48.560Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a3a5ba371e4f4f07; input_fingerprint=e8c0d765a34ef36db3fe300613fff9705dbad1de7fad6b36259a2972b4c3f945 |
| 18070 | 2026-08-18T15:44:48.846Z | managed_process_admitted |  |  | owner=default |
| 18071 | 2026-08-18T15:44:49.078Z | managed_process_started |  |  | owner=default |
| 18072 | 2026-08-18T15:44:49.610Z | managed_process_terminal |  |  | owner=default |
| 18073 | 2026-08-18T15:44:49.894Z | proof_recorded |  |  | stage_id=check:a3a5ba371e4f4f07; status=passed; cache_hit=False; input_fingerprint=e8c0d765a34ef36db3fe300613fff9705dbad1de7fad6b36259a2972b4c3f945 |
| 18074 | 2026-08-18T15:44:50.044Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=734795f26e399669ce39caeec7c9b9b5003b828bab2f3ff0164786b410b76973 |
| 18075 | 2026-08-18T15:44:50.319Z | managed_process_admitted |  |  | owner=default |
| 18076 | 2026-08-18T15:44:50.562Z | managed_process_started |  |  | owner=default |
| 18077 | 2026-08-18T15:45:00.178Z | managed_process_terminal |  |  | owner=default |
| 18078 | 2026-08-18T15:45:01.692Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=734795f26e399669ce39caeec7c9b9b5003b828bab2f3ff0164786b410b76973 |
| 18079 | 2026-08-18T15:45:02.186Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 18080 | 2026-08-18T15:45:57.929Z | managed_process_admitted |  |  | owner=default |
| 18081 | 2026-08-18T15:45:58.162Z | managed_process_started |  |  | owner=default |
| 18082 | 2026-08-18T15:45:58.527Z | managed_process_terminal |  |  | owner=default |
| 18083 | 2026-08-18T15:46:12.594Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 18084 | 2026-08-18T15:46:12.871Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:a3a5ba371e4f4f07 | passed | e8c0d765a34ef36db3fe300613fff9705dbad1de7fad6b36259a2972b4c3f945 | False | 1050 | 0 |
| verify:tests | passed | 734795f26e399669ce39caeec7c9b9b5003b828bab2f3ff0164786b410b76973 | False | 11172 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| b7eb125a94224c3497a9863bbd4266b7 | accepted | b7af2598297870e816dd131b0f73e0f77d7608d5 | cf1dc19b1f5c4b14967b5f69469d2f827410f0e2fd8b7d29a420cfce168085bc | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `28`
- Chain head: `5198f54cff4c17962f750940a1925846d8762a88ca1b7eb1f006f56adb8d786d`
