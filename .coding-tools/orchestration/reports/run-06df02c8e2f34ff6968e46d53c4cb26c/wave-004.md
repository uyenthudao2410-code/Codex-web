# Orchestration Wave 4

- Run: `06df02c8e2f34ff6968e46d53c4cb26c`
- Wave: `10cd99b519f943ce8f984f54503ac65c`
- Objective: Implement and deploy Phase 3 independent Recovery Supervisor for Windows on the current repository head. It must live outside the Electron Recovery Host process and resurrect Recovery Host after total host death without depending on Coding MCP, Tunnel, or Electron UI. Keep it minimal and fail-closed: same-user Scheduled Task, bounded authenticated health polling/backoff/crash-loop suppression, exact app identity, fixed --recovery-host spawn only, no arbitrary command/path/PID surface, no secret disclosure, durable local status. It must not own normal Coding MCP/Tunnel lifecycle. Add deterministic install/uninstall/status commands and tests, then deploy on this machine and prove killing Recovery Host automatically creates a new host while Coding MCP/Tunnel PIDs and MCP identity remain unchanged. Preserve all current-head content and runtime evidence.
- Mode: `mcp_only`
- Base HEAD: `6299c052567852607ddcda30fabe48c859eef932`
- Worktree fingerprint: `25402d5abb7e1ead012b327eb0ff1ee549f47ad4549c5a0e75b83571476cdc79`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 6320 | 2026-08-16T08:42:23.521Z | wave_replanned |  | PREFLIGHT | reason=All production behavior assertions now pass except the dead-host test hook: the short-lived where.exe spawn transiently holds its temp working directory, causing EBUSY during immediate rmdir. The behavior itself reached restart_started. Harden only test cleanup with bounded retryDelay/maxRetries and rerun the unchanged assertions. |
| 6321 | 2026-08-16T08:42:23.655Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 6322 | 2026-08-16T08:42:23.771Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 6323 | 2026-08-16T08:42:23.902Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 6324 | 2026-08-16T08:42:24.026Z | state_transition | READY | ROUTED | reason=route_selected |
| 6325 | 2026-08-16T08:42:24.449Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=08d6927c94754304b328206276ae602e |
| 6326 | 2026-08-16T08:42:24.591Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 6327 | 2026-08-16T08:42:25.058Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=08d6927c94754304b328206276ae602e |
| 6328 | 2026-08-16T08:42:25.149Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 6329 | 2026-08-16T08:42:25.458Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:d9c099758f2ff7c2; input_fingerprint=c4269a1866bb4b1c2f08c40e71c298566741e343e97325ab2cb29093e5bc3c90 |
| 6330 | 2026-08-16T08:42:25.716Z | managed_process_admitted |  |  | owner=default |
| 6331 | 2026-08-16T08:42:25.931Z | managed_process_started |  |  | owner=default |
| 6332 | 2026-08-16T08:42:26.432Z | managed_process_terminal |  |  | owner=default |
| 6333 | 2026-08-16T08:42:26.655Z | proof_recorded |  |  | stage_id=check:d9c099758f2ff7c2; status=passed; cache_hit=False; input_fingerprint=c4269a1866bb4b1c2f08c40e71c298566741e343e97325ab2cb29093e5bc3c90 |
| 6334 | 2026-08-16T08:42:26.791Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:fe3ffbf7aa7a92a6; input_fingerprint=af479ea796a0c106db6f7472fce65358cb4750d9bea1b745ddf719063a73d2c0 |
| 6335 | 2026-08-16T08:42:27.024Z | managed_process_admitted |  |  | owner=default |
| 6336 | 2026-08-16T08:42:27.224Z | managed_process_started |  |  | owner=default |
| 6337 | 2026-08-16T08:42:29.829Z | managed_process_terminal |  |  | owner=default |
| 6338 | 2026-08-16T08:42:30.047Z | proof_recorded |  |  | stage_id=check:fe3ffbf7aa7a92a6; status=failed; cache_hit=False; input_fingerprint=af479ea796a0c106db6f7472fce65358cb4750d9bea1b745ddf719063a73d2c0 |
| 6339 | 2026-08-16T08:42:30.186Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 6340 | 2026-08-16T08:42:30.296Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 6341 | 2026-08-16T08:42:30.454Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:d9c099758f2ff7c2 | passed | c4269a1866bb4b1c2f08c40e71c298566741e343e97325ab2cb29093e5bc3c90 | False | 988 | 0 |
| check:fe3ffbf7aa7a92a6 | failed | af479ea796a0c106db6f7472fce65358cb4750d9bea1b745ddf719063a73d2c0 | False | 3025 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `216`
- Chain head: `2dc6a112f6500c12edabd367a01bc4c847cc606df6cbedc5cbd6d794593a0625`
