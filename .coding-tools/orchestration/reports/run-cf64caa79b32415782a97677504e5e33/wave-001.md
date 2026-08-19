# Orchestration Wave 1

- Run: `cf64caa79b32415782a97677504e5e33`
- Wave: `91e91b288fd84a078b521194f93818f0`
- Objective: Final focused verification for the already-applied concurrent execution-context isolation. Do not modify any source. Verify workspace/session isolation together with Execution Hub reconnect/controller fault behavior and hub proxy stdio compatibility from the package root. Preserve all unrelated work and do not commit, push, restart, deploy, or alter measurement-integrity source.
- Mode: `mcp_only`
- Base HEAD: `7c1c93ea72fa3465d718f7826494629426c1a9e8`
- Worktree fingerprint: `87b30a3e26bb7255143b906bf72bc4cfbe30b1ddd030727c03c1f74476c66806`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 20229 | 2026-08-19T05:33:48.354Z | run_started |  | PREFLIGHT |  |
| 20230 | 2026-08-19T05:33:48.782Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 20231 | 2026-08-19T05:33:49.180Z | managed_process_admitted |  |  | owner=default |
| 20232 | 2026-08-19T05:33:49.438Z | managed_process_started |  |  | owner=default |
| 20233 | 2026-08-19T05:33:52.733Z | managed_process_admitted |  |  | owner=chatweb |
| 20234 | 2026-08-19T05:33:52.988Z | managed_process_started |  |  | owner=chatweb |
| 20235 | 2026-08-19T05:33:54.517Z | managed_process_terminal |  |  | owner=chatweb |
| 20236 | 2026-08-19T05:34:05.414Z | managed_process_terminal |  |  | owner=default |
| 20237 | 2026-08-19T05:34:05.565Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 20238 | 2026-08-19T05:34:05.721Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 20239 | 2026-08-19T05:34:05.860Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 20240 | 2026-08-19T05:34:06.009Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 20241 | 2026-08-19T05:34:06.137Z | state_transition | READY | ROUTED | reason=route_selected |
| 20242 | 2026-08-19T05:34:06.632Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f668988a3a614975b52378ae89b78a5c |
| 20243 | 2026-08-19T05:34:06.800Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 20244 | 2026-08-19T05:34:07.299Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f668988a3a614975b52378ae89b78a5c |
| 20245 | 2026-08-19T05:34:07.433Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 20246 | 2026-08-19T05:34:07.817Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=6be40ed3389615e83b067a8c4d762e86a4c38f3131d7b3ce8e202b23d93cb0b0 |
| 20247 | 2026-08-19T05:34:08.198Z | managed_process_admitted |  |  | owner=default |
| 20248 | 2026-08-19T05:34:08.454Z | managed_process_started |  |  | owner=default |
| 20249 | 2026-08-19T05:34:19.616Z | state_transition | PROVING | ABORTED | reason=Read-only isolation verification completed successfully: 21 focused tests passed, with no source mutation or write lease. Terminalize this diagnostic run so the measurement-integrity implementation can continue without projection contention. |
| 20250 | 2026-08-19T05:34:20.199Z | managed_process_terminal |  |  | owner=default |
| 20251 | 2026-08-19T05:34:20.519Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=6be40ed3389615e83b067a8c4d762e86a4c38f3131d7b3ce8e202b23d93cb0b0 |
| 20252 | 2026-08-19T05:34:20.519Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |
| 20253 | 2026-08-19T05:34:20.821Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 6be40ed3389615e83b067a8c4d762e86a4c38f3131d7b3ce8e202b23d93cb0b0 | False | 12188 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `25`
- Chain head: `708f0e62da6c2f23348529a4cca6e032b8ba2939ba622f68dd575cfba5388e9a`
