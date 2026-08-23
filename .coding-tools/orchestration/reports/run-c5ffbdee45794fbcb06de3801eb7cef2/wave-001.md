# Orchestration Wave 1

- Run: `c5ffbdee45794fbcb06de3801eb7cef2`
- Wave: `1b428d76b4f243d6979bef66e5bedc89`
- Objective: Fix proof-integrity false positives: after a proof command reaches a terminal payload, use execution_owner.job_id to read the exact durable managed-job lifecycle before TaskState/proof reduction. A known lifecycle other than exited (especially quiesced, terminated, timeout, spawn_failed, orphaned) must make the proof non-success even when root status is exited and exit_code is 0. Do not parse stdout for failure text. Preserve current Rust test-only worktree changes. Add deterministic regressions showing exit0+quiesced fails closed and exit0+exited remains pass; keep unmanaged payload compatibility unchanged.
- Objective revision: `1`
- Objective SHA-256: `4761bc127d0ca88f2917dd825ec2d653aa2c0b76179f58231dee24ba660141de`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9e150020a0c0829a988ffea527d5c8d82132ed65`
- Worktree fingerprint: `7b54aa5ab96a3b29ba50523d4283c0e0553d039c6634fd3c18da1cfeab1344ff`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 28616 | 2026-08-23T04:52:56.272Z | run_started |  | PREFLIGHT |  |
| 28617 | 2026-08-23T04:53:09.101Z | solution_shadow_recommended |  |  |  |
| 28618 | 2026-08-23T04:53:23.292Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 28619 | 2026-08-23T04:53:23.465Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 28620 | 2026-08-23T04:53:23.623Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 28621 | 2026-08-23T04:53:23.816Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 28622 | 2026-08-23T04:53:23.978Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 28623 | 2026-08-23T04:53:24.182Z | state_transition | READY | ROUTED | reason=route_selected |
| 28624 | 2026-08-23T04:53:25.041Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=dbff8468da984746ab42b9682a92f4c4 |
| 28625 | 2026-08-23T04:53:25.215Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 28626 | 2026-08-23T04:53:26.061Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=dbff8468da984746ab42b9682a92f4c4 |
| 28627 | 2026-08-23T04:53:26.256Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 28628 | 2026-08-23T04:53:26.934Z | proof_cache_miss |  |  | reason=cold; stage_id=check:7ce94cc0a934985e; input_fingerprint=e83aedcd87b57b40e485c27b4971ad959fb47c05d1ebe3a552673d72e0e339a7 |
| 28629 | 2026-08-23T04:53:27.271Z | managed_process_admitted |  |  | owner=default |
| 28630 | 2026-08-23T04:53:27.449Z | failure_observed | PROVING | PROVING | reason=A non-terminal wave was recovered outside its original synchronous execution.; failure_class=RUNTIME_RESUME_REQUIRED |
| 28631 | 2026-08-23T04:53:27.636Z | state_transition | PROVING | REPLAN | reason=RUNTIME_RESUME_REQUIRED; failure_class=RUNTIME_RESUME_REQUIRED |
| 28632 | 2026-08-23T04:53:27.941Z | managed_process_started |  |  | owner=default |
| 28633 | 2026-08-23T04:53:28.408Z | managed_process_terminal |  |  | owner=default |
| 28634 | 2026-08-23T04:53:28.751Z | proof_recorded |  |  | stage_id=check:7ce94cc0a934985e; status=passed; cache_hit=False; input_fingerprint=e83aedcd87b57b40e485c27b4971ad959fb47c05d1ebe3a552673d72e0e339a7 |
| 28635 | 2026-08-23T04:53:28.907Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 28636 | 2026-08-23T04:53:29.119Z | proof_cache_miss |  |  | reason=cold; stage_id=check:80c72138ea2f0029; input_fingerprint=b5893c803e6e98cd02cc7a58d9fe33061123e92f117fb904031f510634505eb5 |
| 28637 | 2026-08-23T04:53:29.309Z | failure_observed | PROVING | PROVING | failure_class=EXECUTION_OWNER_INVALID |
| 28638 | 2026-08-23T04:53:29.472Z | state_transition | PROVING | REPLAN | reason=EXECUTION_OWNER_INVALID; failure_class=EXECUTION_OWNER_INVALID |
| 28639 | 2026-08-23T04:53:29.671Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:7ce94cc0a934985e | passed | e83aedcd87b57b40e485c27b4971ad959fb47c05d1ebe3a552673d72e0e339a7 | False | 1316 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `122`
- Chain head: `f5d5313275888b2939cb1adf69d54d748815afc26313b27cb59e574bd0f3be47`
