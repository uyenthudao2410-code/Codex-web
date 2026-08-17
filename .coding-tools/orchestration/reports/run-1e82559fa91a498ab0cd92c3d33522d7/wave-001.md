# Orchestration Wave 1

- Run: `1e82559fa91a498ab0cd92c3d33522d7`
- Wave: `4b8f4d87edc941bfa8ba65aa81c8d6c5`
- Objective: Fix the packaged Recovery Supervisor UTF-8 manifest decoding defect proven by the win-unpacked acceptance probe. Write-JsonAtomic emits UTF-8 without BOM, so Read-BoundedJson must decode explicitly as UTF-8 instead of relying on Windows PowerShell 5.1 Get-Content default encoding. Add a focused Windows regression using a packaged-mode manifest whose executable/app_root contain the actual Vietnamese-style Unicode product path; prove Action Once parses it and remains degraded rather than falsely reporting executable missing. Preserve all manifest validation, fail-closed spawn/hash rules, and source behavior otherwise.
- Mode: `mcp_only`
- Base HEAD: `f1b38e6ca8d63c2d07357f0fc88aa1631021c6b1`
- Worktree fingerprint: `f267748441ab698ca7151a45c8bd1db0d3e1dd1691eb89bfaa9508031a7bbefc`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 11930 | 2026-08-17T07:20:14.940Z | run_started |  | PREFLIGHT |  |
| 11931 | 2026-08-17T07:20:15.438Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11932 | 2026-08-17T07:20:15.653Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 11933 | 2026-08-17T07:20:15.855Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 11934 | 2026-08-17T07:20:16.051Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 11935 | 2026-08-17T07:20:16.235Z | state_transition | READY | ROUTED | reason=route_selected |
| 11936 | 2026-08-17T07:20:16.839Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=17ff4a11f1374b2f9cd75e7a673d0761 |
| 11937 | 2026-08-17T07:20:16.994Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 11938 | 2026-08-17T07:20:17.579Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=17ff4a11f1374b2f9cd75e7a673d0761 |
| 11939 | 2026-08-17T07:20:17.812Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 11940 | 2026-08-17T07:20:18.234Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:fe3ffbf7aa7a92a6; input_fingerprint=a19d02c748616004fe3aa5207786bb84ff0bf3c15c461d57b719a3781d76598e |
| 11941 | 2026-08-17T07:20:18.602Z | managed_process_admitted |  |  | owner=default |
| 11942 | 2026-08-17T07:20:18.906Z | managed_process_started |  |  | owner=default |
| 11943 | 2026-08-17T07:20:27.765Z | managed_process_terminal |  |  | owner=default |
| 11944 | 2026-08-17T07:20:28.187Z | proof_recorded |  |  | stage_id=check:fe3ffbf7aa7a92a6; status=passed; cache_hit=False; input_fingerprint=a19d02c748616004fe3aa5207786bb84ff0bf3c15c461d57b719a3781d76598e |
| 11945 | 2026-08-17T07:20:28.391Z | proof_cache_miss |  |  | reason=cold; stage_id=check:d748b3f2c2065ed5; input_fingerprint=018f9d8cfce0e29bbe7b3a3174ba9260b8da4ae3570e9ec5a01f7d53d236a116 |
| 11946 | 2026-08-17T07:20:28.785Z | managed_process_admitted |  |  | owner=default |
| 11947 | 2026-08-17T07:20:29.159Z | managed_process_started |  |  | owner=default |
| 11948 | 2026-08-17T07:20:29.657Z | managed_process_terminal |  |  | owner=default |
| 11949 | 2026-08-17T07:20:29.989Z | proof_recorded |  |  | stage_id=check:d748b3f2c2065ed5; status=passed; cache_hit=False; input_fingerprint=018f9d8cfce0e29bbe7b3a3174ba9260b8da4ae3570e9ec5a01f7d53d236a116 |
| 11950 | 2026-08-17T07:20:30.571Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 11951 | 2026-08-17T07:20:43.472Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 11952 | 2026-08-17T07:20:43.823Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:fe3ffbf7aa7a92a6 | passed | a19d02c748616004fe3aa5207786bb84ff0bf3c15c461d57b719a3781d76598e | False | 9557 | 0 |
| check:d748b3f2c2065ed5 | passed | 018f9d8cfce0e29bbe7b3a3174ba9260b8da4ae3570e9ec5a01f7d53d236a116 | False | 1226 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 045033950b044d32b85c07ab283c69a9 | accepted | f1b38e6ca8d63c2d07357f0fc88aa1631021c6b1 | 3cdc8e741df17e49387e733a769bf57dfaa52b945a4ef631d41b945579afd551 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `7ea5ab86f411b851d8b10d7bb728440b3a4d3ab0674aa631de33d31bdf2896b2`
