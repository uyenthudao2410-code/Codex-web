# Orchestration Wave 5

- Run: `35a4c3e13c094de9b07aef7280df8ebb`
- Wave: `ad7c621cfaa744bf9004be7a6b949060`
- Objective: Run only the first remaining metadata contract regression on the already-patched worktree. No source mutation. This verifies that compact tool_manifest no longer incorrectly requires the deliberately ModelHidden start_coding_task compatibility entry.
- Objective revision: `5`
- Objective SHA-256: `814299070bd58e613c7d64ae1d733f29168b59157b57d3c399002a8b160728b6`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `9e150020a0c0829a988ffea527d5c8d82132ed65`
- Worktree fingerprint: `7b54aa5ab96a3b29ba50523d4283c0e0553d039c6634fd3c18da1cfeab1344ff`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 28450 | 2026-08-23T04:43:03.847Z | wave_replanned |  | PREFLIGHT | reason=Both connector tests now pass on the patched worktree. The controller quiesces multi-command proof waves after each worktree/evidence fingerprint transition, so run the remaining metadata proof as a single-command wave to preserve deterministic evidence. |
| 28451 | 2026-08-23T04:43:04.061Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 28452 | 2026-08-23T04:43:04.217Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 28453 | 2026-08-23T04:43:04.426Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 28454 | 2026-08-23T04:43:04.638Z | state_transition | READY | ROUTED | reason=route_selected |
| 28458 | 2026-08-23T04:43:05.504Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1d06e72eed1344c08f56d0fa6acea526 |
| 28459 | 2026-08-23T04:43:05.678Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 28463 | 2026-08-23T04:43:07.017Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1d06e72eed1344c08f56d0fa6acea526 |
| 28464 | 2026-08-23T04:43:07.201Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 28467 | 2026-08-23T04:43:07.950Z | proof_cache_miss |  |  | reason=cold; stage_id=check:3daa3fba6a03c704; input_fingerprint=62e3a2ba78b8b5cd14c975684a6022372b8a8be55dd3c89cc002915022280f18 |
| 28468 | 2026-08-23T04:43:08.201Z | failure_observed | PROVING | PROVING | failure_class=EXECUTION_OWNER_MISMATCH |
| 28469 | 2026-08-23T04:43:08.427Z | state_transition | PROVING | REPLAN | reason=EXECUTION_OWNER_MISMATCH; failure_class=EXECUTION_OWNER_MISMATCH |
| 28470 | 2026-08-23T04:43:08.647Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `113`
- Chain head: `425ad0b8631e517198bf31f9bad74846f1e83fee2eb80c00690ef5fa481a74c3`
