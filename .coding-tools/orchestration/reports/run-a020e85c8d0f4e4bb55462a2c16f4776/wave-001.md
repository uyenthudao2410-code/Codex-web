# Orchestration Wave 1

- Run: `a020e85c8d0f4e4bb55462a2c16f4776`
- Wave: `a9c7680dd0f44f46a479638f269d1187`
- Objective: Implement the remaining Layer C of P3 validation compute-placement control on the authoritative current checkout. Consume the already-plumbed optional compute_placement_policy for cargo_check/cargo_test only. Explicit selector must reject before enqueue/process unless resolved project is Agent-backed, sandbox is absent, request is long structured validation (effective timeout > sync wait), Runner supports structured async validation handoff, and source is Clean exact-source with a valid exact git head. Unknown selector is already typed/serde rejected. Explicit local_only must force source Runner and never select/call server compute. Explicit server_preferred must use existing clean-source server target selection + revalidation and safe local fallback; caller never supplies runner id. Absent selector must preserve all current production behavior including dirty-snapshot auto-offload. For explicit runs construct ShellJobValidationComputePlacement evidence and persist it in ShellJobValidationMetadata, immediate cargo terminal/handoff result, and job_status/job_log validation projection; absent selector must keep evidence absent. Add focused tests for local_only, server_preferred success/fallback, invalid explicit contexts pre-execution, default absent-selector behavior, projection, and cargo_fmt/schema rejection as needed. Do not modify analyzer/frozen P3 manifest, do not restart runtime, do not enroll representative P3 pairs, and preserve all .coding-tools telemetry plus existing formatting diffs.
- Mode: `mcp_only`
- Base HEAD: `189de19e2f7dbaa2a71ee62dbcc50d5d76a55c0a`
- Worktree fingerprint: `942fe30da7ec0e3ea2c37f83b52070d0b7a0da6568fc43763e7b9e7ec5e9e010`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 16270 | 2026-08-18T00:20:10.178Z | run_started |  | PREFLIGHT |  |
| 16271 | 2026-08-18T00:20:15.540Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 16272 | 2026-08-18T00:21:18.948Z | managed_process_admitted |  |  | owner=default |
| 16273 | 2026-08-18T00:21:19.193Z | managed_process_started |  |  | owner=default |
| 16274 | 2026-08-18T00:21:20.639Z | managed_process_terminal |  |  | owner=default |
| 16275 | 2026-08-18T00:21:30.276Z | managed_process_admitted |  |  | owner=default |
| 16276 | 2026-08-18T00:21:30.493Z | managed_process_started |  |  | owner=default |
| 16277 | 2026-08-18T00:21:31.081Z | managed_process_terminal |  |  | owner=default |
| 16278 | 2026-08-18T00:21:39.945Z | managed_process_admitted |  |  | owner=default |
| 16279 | 2026-08-18T00:21:40.173Z | managed_process_started |  |  | owner=default |
| 16280 | 2026-08-18T00:21:40.602Z | managed_process_terminal |  |  | owner=default |
| 16281 | 2026-08-18T00:22:04.454Z | failure_observed | PREFLIGHT | PREFLIGHT | failure_class=BASE_DRIFT |
| 16282 | 2026-08-18T00:22:04.559Z | state_transition | PREFLIGHT | REPLAN | reason=BASE_DRIFT; failure_class=BASE_DRIFT |
| 16283 | 2026-08-18T00:22:04.692Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `37`
- Chain head: `80f89457e4769c21bc819a46143fea080f6e565c1b7749ef49a9cf646495efc1`
