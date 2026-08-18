# Orchestration Wave 2

- Run: `914960cc74f0406c82c52ace1ffd6b3a`
- Wave: `0148adaac09140e39d50b7e2b1ebe1b7`
- Objective: Continue Layer C after accepted C1a on the current authoritative checkout. Wire explicit compute_placement_policy guards into run_readonly_validation and run_readonly_validation_agent; explicit selector only for long unsandboxed Agent-backed structured-job capable clean exact-source cargo_check/test. Implement local_only forcing source with no remote target selection and server_preferred using existing clean target selection/revalidation plus source fallback. Build ShellJobValidationComputePlacement from actual executor, persist it in ShellJobValidationMetadata and ValidationHandoff. Do not yet add tests in this wave beyond compile proof; selector absent must preserve current auto-offload behavior. Preserve all telemetry/concurrent commits. No analyzer/manifest/restart/P3 enrollment.
- Mode: `mcp_only`
- Base HEAD: `17e87d34b159cbc175a77bb041e670000c9f7f4b`
- Worktree fingerprint: `e86891942b708998507d2eb9103f4ef1349a970474e477f896d97fb0a43f8631`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 16323 | 2026-08-18T00:26:39.889Z | wave_replanned |  | PREFLIGHT | reason=The explicit sol_xhigh candidate hit its 30-second model deadline before producing any candidate or source mutation. Strategy changes to a small deterministic patch over already-localized existing control flow, with focused proof after each coherent mutation. |
| 16324 | 2026-08-18T00:26:45.279Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 16325 | 2026-08-18T00:27:43.806Z | managed_process_admitted |  |  | owner=default |
| 16326 | 2026-08-18T00:27:44.072Z | managed_process_started |  |  | owner=default |
| 16327 | 2026-08-18T00:27:44.588Z | managed_process_terminal |  |  | owner=default |
| 16328 | 2026-08-18T00:27:58.969Z | managed_process_admitted |  |  | owner=default |
| 16329 | 2026-08-18T00:27:59.189Z | managed_process_started |  |  | owner=default |
| 16330 | 2026-08-18T00:27:59.536Z | managed_process_terminal |  |  | owner=default |
| 16331 | 2026-08-18T00:28:06.764Z | managed_process_admitted |  |  | owner=default |
| 16332 | 2026-08-18T00:28:06.947Z | managed_process_started |  |  | owner=default |
| 16333 | 2026-08-18T00:28:07.314Z | managed_process_terminal |  |  | owner=default |
| 16334 | 2026-08-18T00:28:41.964Z | managed_process_admitted |  |  | owner=default |
| 16335 | 2026-08-18T00:28:42.230Z | managed_process_started |  |  | owner=default |
| 16336 | 2026-08-18T00:28:43.061Z | managed_process_terminal |  |  | owner=default |
| 16337 | 2026-08-18T00:29:02.967Z | managed_process_admitted |  |  | owner=default |
| 16338 | 2026-08-18T00:29:03.202Z | managed_process_started |  |  | owner=default |
| 16339 | 2026-08-18T00:29:03.544Z | managed_process_terminal |  |  | owner=default |
| 16340 | 2026-08-18T00:29:10.497Z | managed_process_admitted |  |  | owner=default |
| 16341 | 2026-08-18T00:29:10.711Z | managed_process_started |  |  | owner=default |
| 16342 | 2026-08-18T00:29:11.072Z | managed_process_terminal |  |  | owner=default |
| 16343 | 2026-08-18T00:29:18.772Z | managed_process_admitted |  |  | owner=default |
| 16344 | 2026-08-18T00:29:19.013Z | managed_process_started |  |  | owner=default |
| 16345 | 2026-08-18T00:29:19.371Z | managed_process_terminal |  |  | owner=default |
| 16346 | 2026-08-18T00:30:03.585Z | managed_process_admitted |  |  | owner=default |
| 16347 | 2026-08-18T00:30:03.788Z | managed_process_started |  |  | owner=default |
| 16348 | 2026-08-18T00:30:04.163Z | managed_process_terminal |  |  | owner=default |
| 16349 | 2026-08-18T00:30:11.698Z | managed_process_admitted |  |  | owner=default |
| 16350 | 2026-08-18T00:30:11.935Z | managed_process_started |  |  | owner=default |
| 16351 | 2026-08-18T00:30:12.913Z | managed_process_terminal |  |  | owner=default |
| 16352 | 2026-08-18T00:30:19.250Z | managed_process_admitted |  |  | owner=default |
| 16353 | 2026-08-18T00:30:19.483Z | managed_process_started |  |  | owner=default |
| 16354 | 2026-08-18T00:30:20.022Z | managed_process_terminal |  |  | owner=default |
| 16355 | 2026-08-18T00:31:28.854Z | managed_process_admitted |  |  | owner=default |
| 16356 | 2026-08-18T00:31:29.080Z | managed_process_started |  |  | owner=default |
| 16357 | 2026-08-18T00:31:29.630Z | managed_process_terminal |  |  | owner=default |
| 16358 | 2026-08-18T00:31:45.393Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 16359 | 2026-08-18T00:31:45.502Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 16360 | 2026-08-18T00:31:45.631Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 16361 | 2026-08-18T00:31:45.755Z | state_transition | READY | ROUTED | reason=route_selected |
| 16362 | 2026-08-18T00:31:46.116Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f44581f50e9c4d369619e9544c8741fe |
| 16363 | 2026-08-18T00:31:46.231Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 16364 | 2026-08-18T00:31:46.623Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f44581f50e9c4d369619e9544c8741fe |
| 16365 | 2026-08-18T00:31:46.858Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 16366 | 2026-08-18T00:31:47.181Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:e78d1497906c3031; input_fingerprint=2e7974dd3b89c35a9ee23e26b3b5a42450dc8b6aed7e43d3b2a9f7719aada2d3 |
| 16367 | 2026-08-18T00:31:47.438Z | managed_process_admitted |  |  | owner=default |
| 16368 | 2026-08-18T00:31:47.649Z | managed_process_started |  |  | owner=default |
| 16369 | 2026-08-18T00:31:48.005Z | managed_process_terminal |  |  | owner=default |
| 16370 | 2026-08-18T00:31:48.213Z | proof_recorded |  |  | stage_id=check:e78d1497906c3031; status=passed; cache_hit=False; input_fingerprint=2e7974dd3b89c35a9ee23e26b3b5a42450dc8b6aed7e43d3b2a9f7719aada2d3 |
| 16371 | 2026-08-18T00:31:48.324Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:810e75f0d3dee10e; input_fingerprint=f7a056c33dabb01ad78f7c82a80d19bfb44ff00d7ebd67a3a043d3e2957f1b61 |
| 16372 | 2026-08-18T00:31:48.566Z | managed_process_admitted |  |  | owner=default |
| 16373 | 2026-08-18T00:31:48.758Z | managed_process_started |  |  | owner=default |
| 16374 | 2026-08-18T00:31:53.791Z | managed_process_terminal |  |  | owner=default |
| 16375 | 2026-08-18T00:31:54.030Z | proof_recorded |  |  | stage_id=check:810e75f0d3dee10e; status=failed; cache_hit=False; input_fingerprint=f7a056c33dabb01ad78f7c82a80d19bfb44ff00d7ebd67a3a043d3e2957f1b61 |
| 16376 | 2026-08-18T00:31:54.140Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 16377 | 2026-08-18T00:31:54.242Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 16378 | 2026-08-18T00:31:54.376Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:e78d1497906c3031 | passed | 2e7974dd3b89c35a9ee23e26b3b5a42450dc8b6aed7e43d3b2a9f7719aada2d3 | False | 810 | 0 |
| check:810e75f0d3dee10e | failed | f7a056c33dabb01ad78f7c82a80d19bfb44ff00d7ebd67a3a043d3e2957f1b61 | False | 5480 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `105`
- Chain head: `35dc75a3c181ef05008301c28a66e545f0d1f1626e437e6c88d18e4d60fcfe12`
