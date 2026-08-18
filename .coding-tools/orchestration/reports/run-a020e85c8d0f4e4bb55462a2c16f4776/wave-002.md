# Orchestration Wave 2

- Run: `a020e85c8d0f4e4bb55462a2c16f4776`
- Wave: `7ae51200746b4f2285b9fdd8c1938177`
- Objective: Implement the remaining Layer C of P3 validation compute-placement control on the authoritative current checkout. Consume the already-plumbed optional compute_placement_policy for cargo_check/cargo_test only. Explicit selector must reject before enqueue/process unless resolved project is Agent-backed, sandbox is absent, request is long structured validation (effective timeout > sync wait), Runner supports structured async validation handoff, and source is Clean exact-source with a valid exact git head. Unknown selector is already typed/serde rejected. Explicit local_only must force source Runner and never select/call server compute. Explicit server_preferred must use existing clean-source server target selection + revalidation and safe local fallback; caller never supplies runner id. Absent selector must preserve all current production behavior including dirty-snapshot auto-offload. For explicit runs construct ShellJobValidationComputePlacement evidence and persist it in ShellJobValidationMetadata, immediate cargo terminal/handoff result, and job_status/job_log validation projection; absent selector must keep evidence absent. Add focused tests for local_only, server_preferred success/fallback, invalid explicit contexts pre-execution, default absent-selector behavior, projection, and cargo_fmt/schema rejection as needed. Do not modify analyzer/frozen P3 manifest, do not restart runtime, do not enroll representative P3 pairs, and preserve all .coding-tools telemetry plus existing formatting diffs.
- Mode: `mcp_only`
- Base HEAD: `17e87d34b159cbc175a77bb041e670000c9f7f4b`
- Worktree fingerprint: `b4665f6b3dee0d10d13e9cfaf631bba5aee9a43242dab4aa75bcf11d9ac7ae29`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 16284 | 2026-08-18T00:22:05.003Z | wave_replanned |  | PREFLIGHT | reason=Authoritative main/origin advanced concurrently to 17e87d34 after the prior read-only preflight. No Layer C source mutation occurred. Re-ground on the exact current HEAD and preserve all concurrent commits without reset/rebase/restore. |
| 16285 | 2026-08-18T00:22:09.982Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 16286 | 2026-08-18T00:22:54.329Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 16287 | 2026-08-18T00:22:54.439Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 16288 | 2026-08-18T00:22:54.563Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 16289 | 2026-08-18T00:22:54.701Z | state_transition | READY | ROUTED | reason=route_selected |
| 16290 | 2026-08-18T00:22:55.092Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c7de41b03d8d46e282c96f5c4d6d434a |
| 16291 | 2026-08-18T00:22:55.209Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 16292 | 2026-08-18T00:22:55.667Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c7de41b03d8d46e282c96f5c4d6d434a |
| 16293 | 2026-08-18T00:22:55.801Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 16294 | 2026-08-18T00:22:56.125Z | proof_cache_miss |  |  | reason=cold; stage_id=check:9e64db9db6199f2e; input_fingerprint=72030a15e81bce9141821416274883676a4fc308beaff080fcdcfadcf40d0baa |
| 16295 | 2026-08-18T00:22:56.349Z | managed_process_admitted |  |  | owner=default |
| 16296 | 2026-08-18T00:22:56.573Z | managed_process_started |  |  | owner=default |
| 16297 | 2026-08-18T00:22:56.923Z | managed_process_terminal |  |  | owner=default |
| 16298 | 2026-08-18T00:22:57.190Z | proof_recorded |  |  | stage_id=check:9e64db9db6199f2e; status=passed; cache_hit=False; input_fingerprint=72030a15e81bce9141821416274883676a4fc308beaff080fcdcfadcf40d0baa |
| 16299 | 2026-08-18T00:22:57.319Z | proof_cache_miss |  |  | reason=cold; stage_id=check:e78d1497906c3031; input_fingerprint=fcca6551793e5f31befd8ad3868c47304fe18193312f9eafd3683a6eabbbd38a |
| 16300 | 2026-08-18T00:22:57.596Z | managed_process_admitted |  |  | owner=default |
| 16301 | 2026-08-18T00:22:57.831Z | managed_process_started |  |  | owner=default |
| 16302 | 2026-08-18T00:22:58.189Z | managed_process_terminal |  |  | owner=default |
| 16303 | 2026-08-18T00:22:58.433Z | proof_recorded |  |  | stage_id=check:e78d1497906c3031; status=passed; cache_hit=False; input_fingerprint=fcca6551793e5f31befd8ad3868c47304fe18193312f9eafd3683a6eabbbd38a |
| 16304 | 2026-08-18T00:22:58.875Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 16305 | 2026-08-18T00:23:07.858Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 16306 | 2026-08-18T00:23:08.122Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:9e64db9db6199f2e | passed | 72030a15e81bce9141821416274883676a4fc308beaff080fcdcfadcf40d0baa | False | 839 | 0 |
| check:e78d1497906c3031 | passed | fcca6551793e5f31befd8ad3868c47304fe18193312f9eafd3683a6eabbbd38a | False | 887 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 189ab5dcf8ff49c090c1b6969105ae1e | accepted | 17e87d34b159cbc175a77bb041e670000c9f7f4b | 03d6060beffd13381548eb210d9c88c8324411c9fce48d70286434c0a02014d7 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `37`
- Chain head: `80f89457e4769c21bc819a46143fea080f6e565c1b7749ef49a9cf646495efc1`
