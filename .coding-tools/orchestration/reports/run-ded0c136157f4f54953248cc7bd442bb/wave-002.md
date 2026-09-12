# Orchestration Wave 2

- Run: `ded0c136157f4f54953248cc7bd442bb`
- Wave: `6104d1720b614d5d9e59e4e20c92672f`
- Objective: Converge Recovery Host and Coding MCP component state without source writes by no-patch provenance adoption of the runtime-observed Git-dirty subset and exact controller attestation of all 26 current component-file bytes, with fresh bounded deterministic proof covering both runtime components.
- Objective revision: `1`
- Objective SHA-256: `c2cd91d8e4895328f5c5bbcef1b9125cadf5f87d6b23062146ebfefb3eee22b3`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `c1cab4fb02990a1430fe0a09bc30714357ae3344c7d25a3365d4f0f2b7e0268d`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 44292 | 2026-09-08T18:14:34.796Z | wave_replanned |  | PREFLIGHT | reason=The previous full and focused Python processes both completed exit 0 with fresh cache_hit=false proof, but the wrapper deadline expired; preserve the valid Node proof 80c83193261e4e1cab63eaa50d956486 and Python proofs f89fc9f17aa749669d0edca6216f6319 plus 3cd6990ccbb948d696dca5baffcaff0a as supporting exact-byte evidence, and replace only the timed/missing current nodes with a bounded smoke oracle and the missing diff check. |
| 44293 | 2026-09-08T18:14:35.096Z | observation_span_recorded |  |  |  |
| 44294 | 2026-09-08T18:14:35.254Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 44295 | 2026-09-08T18:14:35.423Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 44296 | 2026-09-08T18:14:35.582Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 44297 | 2026-09-08T18:14:36.083Z | state_transition | READY | ROUTED | reason=route_selected |
| 44298 | 2026-09-08T18:14:36.277Z | observation_span_recorded |  |  |  |
| 44299 | 2026-09-08T18:14:37.097Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=db5b75378ffb4e159878758e4798780b |
| 44300 | 2026-09-08T18:14:37.286Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 44301 | 2026-09-08T18:14:38.049Z | existing_file_adoption_observed |  |  |  |
| 44302 | 2026-09-08T18:14:38.232Z | observation_span_recorded |  |  |  |
| 44303 | 2026-09-08T18:14:38.562Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=db5b75378ffb4e159878758e4798780b |
| 44304 | 2026-09-08T18:14:38.728Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 44305 | 2026-09-08T18:14:39.508Z | proof_cache_miss |  |  | reason=cold; stage_id=check:59bfeb5052952719; input_fingerprint=4787206b4771c11937c544083e67978a09c0e01bc4d4b1894b181cca506e3897 |
| 44306 | 2026-09-08T18:14:39.853Z | managed_process_admitted |  |  | owner=default |
| 44307 | 2026-09-08T18:14:40.239Z | managed_process_started |  |  | owner=default |
| 44308 | 2026-09-08T18:14:41.494Z | managed_process_terminal |  |  | owner=default |
| 44309 | 2026-09-08T18:14:41.844Z | proof_recorded |  |  | stage_id=check:59bfeb5052952719; status=failed; cache_hit=False; input_fingerprint=4787206b4771c11937c544083e67978a09c0e01bc4d4b1894b181cca506e3897 |
| 44310 | 2026-09-08T18:14:42.056Z | observation_span_recorded |  |  |  |
| 44311 | 2026-09-08T18:14:42.285Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 44312 | 2026-09-08T18:14:42.511Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 44313 | 2026-09-08T18:14:42.788Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:59bfeb5052952719 | failed | 4787206b4771c11937c544083e67978a09c0e01bc4d4b1894b181cca506e3897 | False | 2018 | 4 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `168`
- Chain head: `23362491c5805f3969b52278a3f6c35b09a28a327a3b674d97f7b5982b40bc9d`
