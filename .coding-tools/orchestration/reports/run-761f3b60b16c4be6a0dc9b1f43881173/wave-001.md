# Orchestration Wave 1

- Run: `761f3b60b16c4be6a0dc9b1f43881173`
- Wave: `2dd31a4c8b234b07be9c1b8525949dec`
- Objective: Run the focused R2B behavior oracle on the current already-compiled source without modifying files. Execute all tests whose names contain server_first_ with one test thread. Acceptance requires the command exit 0 and output demonstrating the new server-first tests actually ran (not zero tests): distinct opted-in exact target dispatch, source runner never selected as compute target, ineligible candidates fall back to source, and offload scope excludes cargo_fmt/short/sandboxed validation. Then run runtime_status_agent_summary_includes_protocol_version to validate observability reports server_preferred/dispatch_enabled=true. Do not run the full test suite and do not mutate source.
- Mode: `mcp_only`
- Base HEAD: `cf6cb6ddbf29d90515d003ce72490ffda985c37f`
- Worktree fingerprint: `bceb4863da8c2f5d82989c8423838aab2c70b794f8bd1a23e4ef694a9a33368f`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 8387 | 2026-08-16T13:17:06.297Z | run_started |  | PREFLIGHT |  |
| 8388 | 2026-08-16T13:17:06.755Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 8389 | 2026-08-16T13:17:06.955Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 8390 | 2026-08-16T13:17:07.062Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 8391 | 2026-08-16T13:17:07.172Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 8392 | 2026-08-16T13:17:07.288Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 8393 | 2026-08-16T13:17:07.391Z | state_transition | READY | ROUTED | reason=route_selected |
| 8394 | 2026-08-16T13:17:07.940Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=25911e6d6ab340e0b502cff53602cf8c |
| 8395 | 2026-08-16T13:17:08.049Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 8396 | 2026-08-16T13:17:08.548Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=25911e6d6ab340e0b502cff53602cf8c |
| 8397 | 2026-08-16T13:17:08.674Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 8398 | 2026-08-16T13:17:09.225Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a81d82c981d723e8; input_fingerprint=6edea059e2e4d74a614b35bdbe8cea53d2898caacc364543198a72ae0ddd79a8 |
| 8399 | 2026-08-16T13:17:09.495Z | managed_process_admitted |  |  | owner=default |
| 8400 | 2026-08-16T13:17:09.871Z | managed_process_started |  |  | owner=default |
| 8401 | 2026-08-16T13:27:10.168Z | managed_process_terminal |  |  | owner=default |
| 8402 | 2026-08-16T13:27:10.472Z | proof_recorded |  |  | stage_id=check:a81d82c981d723e8; status=passed; cache_hit=False; input_fingerprint=6edea059e2e4d74a614b35bdbe8cea53d2898caacc364543198a72ae0ddd79a8 |
| 8403 | 2026-08-16T13:27:10.617Z | proof_cache_miss |  |  | reason=cold; stage_id=check:6496be3777d78431; input_fingerprint=c328ad09c32163735c990874511cae2f06edc6c24cfd86fefd6cbb7dc7fc3c2a |
| 8404 | 2026-08-16T13:27:11.062Z | managed_process_admitted |  |  | owner=default |
| 8405 | 2026-08-16T13:27:11.360Z | managed_process_started |  |  | owner=default |
| 8406 | 2026-08-16T13:28:23.075Z | managed_process_terminal |  |  | owner=default |
| 8407 | 2026-08-16T13:28:23.469Z | proof_recorded |  |  | stage_id=check:6496be3777d78431; status=passed; cache_hit=False; input_fingerprint=c328ad09c32163735c990874511cae2f06edc6c24cfd86fefd6cbb7dc7fc3c2a |
| 8408 | 2026-08-16T13:28:23.590Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 8409 | 2026-08-16T13:28:31.321Z | state_transition | ACCEPTING | ABORTED | reason=Focused root behavior proof could not produce trustworthy test-harness evidence within the 600s workflow envelope; first command crossed the deadline and the second was terminated during link. No source mutation occurred in this proof run. Close it and switch to a smaller deterministic oracle rather than retrying the same monolithic test binary. |
| 8410 | 2026-08-16T13:28:31.618Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:a81d82c981d723e8 | passed | 6edea059e2e4d74a614b35bdbe8cea53d2898caacc364543198a72ae0ddd79a8 | False | 600977 | 0 |
| check:6496be3777d78431 | passed | c328ad09c32163735c990874511cae2f06edc6c24cfd86fefd6cbb7dc7fc3c2a | False | 72334 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `24`
- Chain head: `061bb15cd0fc8a14707776f4b86c743e1c63cb504a7f65893e8491fe62347d4d`
