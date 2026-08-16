# Orchestration Wave 1

- Run: `ae9ac4714f3748008b2cb5830c2efd68`
- Wave: `73f2b490b00f4bb39f4435279d6ff662`
- Objective: Locate the actual launcher/owner of the live internal cmd.exe -> node.exe service without assuming class or file names. Search the whole repository for the configured native LSP provider identifier and Node/LSP launch literals, plus the controlled runtime restart implementation. Read-only only.
- Mode: `mcp_only`
- Base HEAD: `cf6cb6ddbf29d90515d003ce72490ffda985c37f`
- Worktree fingerprint: `9d90a03f02675084e09700ae8a40a88d80a13c097c053935d1c43d49d389b6c5`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 8591 | 2026-08-16T14:11:06.535Z | run_started |  | PREFLIGHT |  |
| 8592 | 2026-08-16T14:11:06.650Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 8593 | 2026-08-16T14:11:06.754Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 8594 | 2026-08-16T14:11:06.900Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 8595 | 2026-08-16T14:11:07.111Z | state_transition | READY | ROUTED | reason=route_selected |
| 8596 | 2026-08-16T14:11:07.550Z | managed_process_admitted |  |  | owner=default |
| 8597 | 2026-08-16T14:11:07.816Z | managed_process_started |  |  | owner=default |
| 8598 | 2026-08-16T14:11:08.039Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a6c4d6c4f68a42ca819cbf75de87863b |
| 8599 | 2026-08-16T14:11:08.184Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 8600 | 2026-08-16T14:11:08.272Z | managed_process_terminal |  |  | owner=default |
| 8601 | 2026-08-16T14:11:08.840Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a6c4d6c4f68a42ca819cbf75de87863b |
| 8602 | 2026-08-16T14:11:08.948Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 8603 | 2026-08-16T14:11:09.522Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ec3efbf7118e85af; input_fingerprint=89adbdab355024e85671402373995e15bc54095a48f4e16a8bb6a1e9e910624a |
| 8604 | 2026-08-16T14:11:09.682Z | failure_observed | PROVING | PROVING | failure_class=INVALID_ARGUMENT |
| 8605 | 2026-08-16T14:11:09.802Z | state_transition | PROVING | REPLAN | reason=INVALID_ARGUMENT; failure_class=INVALID_ARGUMENT |
| 8606 | 2026-08-16T14:11:09.972Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `79`
- Chain head: `27fd9543ea084700b9e57ce7a42d81aaf8f80eb53ce9c0d7f1f4e553d242c9af`
