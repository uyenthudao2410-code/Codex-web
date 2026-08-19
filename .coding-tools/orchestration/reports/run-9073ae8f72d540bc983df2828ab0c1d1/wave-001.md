# Orchestration Wave 1

- Run: `9073ae8f72d540bc983df2828ab0c1d1`
- Wave: `3831c023e19645bb8e498be8a6c64bb7`
- Objective: Complete concurrent multi-project execution-context isolation in E:\DEV\Codex-web without breaking the intended multi-root UI contract. Root cause already proven: HTTP MCP sessions currently alias one shared Runtime whose TaskStateStore and projection helpers are workspace-global, so independent ChatWeb tabs/projects can overwrite task-state.json/projection and can accidentally fall back to another tab's current_active_run. Keep one shared Runtime/process, orchestration ledger, resource governor, command registry, and authorizedRoots semantics. Introduce a lightweight stable execution-context/task projection scope for stateful MCP clients so independent tabs/sessions have isolated TaskStateStore projections while reconnect/aliases for the same logical context can resume. Legacy/stateless clients must remain compatible and may use the legacy workspace-global projection when no stable context exists. Scope must propagate into long-running/background agent_workflow workers, not only HTTP thread-local request handling. A scoped context with no projected run must never fall back to an unrelated workspace-global current_active_run. When a new orchestration run is created for a scoped ChatWeb context, controller ownership must bind to the initiating scoped controller identity so another tab cannot opportunistically claim it. Authorized roots remain valid full execution roots and must not invalidate primary-workspace session scope; actual primary workspace switch still invalidates stale workspace-scoped sessions. Preserve all existing unrelated worktree changes, P4/economics changes, renderer changes, telemetry and docs; do not reset/restore/clean, commit, push, restart or deploy. Keep smart-v3 exactly 8 public tools. Add focused regression tests proving: (1) two independent stateful ChatWeb sessions in the same primary workspace can start different tasks/runs and each reads its own projection, (2) actions in session B do not mutate session A's task state/events/run projection, (3) background agent_workflow retains the initiating execution context, (4) a scoped empty context does not attach to another active run, (5) authorized-root execution remains valid without switching the primary workspace, (6) same-context reconnect continuity remains valid, (7) actual workspace switch rejects stale scoped sessions, and (8) legacy unscoped/sessionless compatibility remains intact. Also replace the positive authorized-root regression command using inline `python -c` with a harmless command allowed by the safe permission mode (for example `python --version`) so the oracle tests product semantics rather than permission escalation.
- Mode: `mcp_only`
- Base HEAD: `7c1c93ea72fa3465d718f7826494629426c1a9e8`
- Worktree fingerprint: `c265ce7da9d6bbdcf5774ec02ec7f8d2919895fd9987487390997bdd844f2132`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 20152 | 2026-08-19T05:27:06.765Z | run_started |  | PREFLIGHT |  |
| 20153 | 2026-08-19T05:27:07.790Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 20154 | 2026-08-19T05:27:07.929Z | managed_process_admitted |  |  | owner=chatweb |
| 20155 | 2026-08-19T05:27:09.646Z | managed_process_started |  |  | owner=chatweb |
| 20156 | 2026-08-19T05:27:09.862Z | managed_process_admitted |  |  | owner=default |
| 20157 | 2026-08-19T05:27:10.461Z | managed_process_started |  |  | owner=default |
| 20158 | 2026-08-19T05:27:10.612Z | managed_process_terminal |  |  | owner=chatweb |
| 20159 | 2026-08-19T05:27:11.772Z | managed_process_terminal |  |  | owner=default |
| 20160 | 2026-08-19T05:27:11.900Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 20161 | 2026-08-19T05:27:12.063Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 20162 | 2026-08-19T05:27:12.296Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 20163 | 2026-08-19T05:27:12.555Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 20164 | 2026-08-19T05:27:12.689Z | state_transition | READY | ROUTED | reason=route_selected |
| 20165 | 2026-08-19T05:27:13.206Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=5eab5c0c88944311a5370591ff885222 |
| 20166 | 2026-08-19T05:27:13.379Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 20167 | 2026-08-19T05:27:13.864Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=5eab5c0c88944311a5370591ff885222 |
| 20168 | 2026-08-19T05:27:14.011Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 20169 | 2026-08-19T05:27:14.441Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=1fdaaab5a6bad72831e644d30d2a396b1f557c6eabcd95d5438e1bd4cb9bdd68 |
| 20170 | 2026-08-19T05:27:14.729Z | managed_process_admitted |  |  | owner=default |
| 20171 | 2026-08-19T05:27:15.045Z | managed_process_started |  |  | owner=default |
| 20172 | 2026-08-19T05:27:16.195Z | managed_process_terminal |  |  | owner=default |
| 20173 | 2026-08-19T05:27:16.589Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=1fdaaab5a6bad72831e644d30d2a396b1f557c6eabcd95d5438e1bd4cb9bdd68 |
| 20174 | 2026-08-19T05:27:16.712Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 20175 | 2026-08-19T05:27:16.909Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 20176 | 2026-08-19T05:27:17.088Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 20177 | 2026-08-19T05:27:44.962Z | state_transition | REPLAN | ABORTED | reason=Superseded by the user's consolidated measurement-integrity implementation. This run is already REPLAN after failed test collection, has no accepted checkpoint or durable source receipts, no active write lease, and no active command. Preserve all source/telemetry; replace it with one integrated wave instead of retrying the failed strategy. |
| 20178 | 2026-08-19T05:27:45.280Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 1fdaaab5a6bad72831e644d30d2a396b1f557c6eabcd95d5438e1bd4cb9bdd68 | False | 1875 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `4091f4a9bc31f54209a862599a970ccad4bf78e951b0134b7bc818d05cc83691`
