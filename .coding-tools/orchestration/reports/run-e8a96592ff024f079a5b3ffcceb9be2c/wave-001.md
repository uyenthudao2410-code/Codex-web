# Orchestration Wave 1

- Run: `e8a96592ff024f079a5b3ffcceb9be2c`
- Wave: `67827748f6c246f4b31d38c703c6b2fa`
- Objective: C4 corrective Wave 2: honor Electron's explicit --user-data-dir only for Recovery Host mode so isolated packaged recovery uses its temporary profile; preserve the existing production %APPDATA%\web-mcp-assistant pin for normal UI and Recovery Host launches without an explicit override. Add a focused pure regression test. Do not modify the packaged smoke harness or unrelated files.
- Objective revision: `1`
- Objective SHA-256: `4ae6c22a20a05887f425152cca37fb1cb0ebe42c4036e65c3ef248ea3f3eae7f`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9b3241ddc963a77d916edc453ea7b7e8e4ae5391`
- Worktree fingerprint: `fdd8e149738afdf61018d6d549f8cfa27ec4acd6f0b714ea56d1e423ae2eeeb6`
- Contract fingerprint: `4aada5917b37cd5c5064b1b1917a78d3ac21fae6f1d94004fcc6dc3222202822`
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 41343 | 2026-09-06T04:29:58.721Z | run_started |  | PREFLIGHT |  |
| 41344 | 2026-09-06T04:29:59.155Z | observation_span_recorded |  |  |  |
| 41345 | 2026-09-06T04:29:59.392Z | solution_shadow_recommended |  |  |  |
| 41346 | 2026-09-06T04:29:59.592Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 41347 | 2026-09-06T04:29:59.756Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 41348 | 2026-09-06T04:29:59.941Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 41349 | 2026-09-06T04:30:00.113Z | state_transition | READY | ROUTED | reason=route_selected |
| 41350 | 2026-09-06T04:30:00.383Z | observation_span_recorded |  |  |  |
| 41351 | 2026-09-06T04:30:01.582Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f232265ca1fa4e2b89735085bce6c871 |
| 41352 | 2026-09-06T04:30:01.760Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 41353 | 2026-09-06T04:30:02.768Z | patch_surface_observed |  |  |  |
| 41354 | 2026-09-06T04:30:03.012Z | observation_span_recorded |  |  |  |
| 41355 | 2026-09-06T04:30:03.309Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f232265ca1fa4e2b89735085bce6c871 |
| 41356 | 2026-09-06T04:30:03.499Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 41357 | 2026-09-06T04:30:04.396Z | proof_cache_miss |  |  | reason=cold; stage_id=check:2904b14d403dbf77; input_fingerprint=98eb2cfac915a848fc71f1e37a1ea64b680b5ece6c17a0546e8da9507271a39e |
| 41358 | 2026-09-06T04:30:04.830Z | managed_process_admitted |  |  | owner=default |
| 41359 | 2026-09-06T04:30:05.130Z | managed_process_started |  |  | owner=default |
| 41360 | 2026-09-06T04:30:05.574Z | managed_process_terminal |  |  | owner=default |
| 41361 | 2026-09-06T04:30:05.932Z | proof_recorded |  |  | stage_id=check:2904b14d403dbf77; status=passed; cache_hit=False; input_fingerprint=98eb2cfac915a848fc71f1e37a1ea64b680b5ece6c17a0546e8da9507271a39e |
| 41362 | 2026-09-06T04:30:06.871Z | observation_span_recorded |  |  |  |
| 41363 | 2026-09-06T04:30:07.077Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 41364 | 2026-09-06T04:30:23.829Z | state_transition | ACCEPTING | ABORTED | reason=Abort unintended detached RUN created by explicit objective mismatch during C4 Wave 2 execute. The user requires all corrective work under existing RUN 3ddeec792a9e4ad589567f0e147c2630. Preserve the three patch bytes for exact-hash adoption into canonical Wave 81838aca67424805b5c31c7c7955ea0f; do not accept this detached run and do not revert unrelated or adopted source. |
| 41365 | 2026-09-06T04:30:24.287Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:2904b14d403dbf77 | passed | 98eb2cfac915a848fc71f1e37a1ea64b680b5ece6c17a0546e8da9507271a39e | False | 1114 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `61f0a366bc4f7180f0bbcb9870fe85064c814e908895bc616dc00c9fe8bd00a6`
