# Orchestration Wave 1

- Run: `88f11555efc9416f88f8d6f100fd6fc4`
- Wave: `0ffaf7fb98e14523adb1b816945c6121`
- Objective: Fix the task_control public contract defect in E:\DEV\Codex-web. Live evidence shows the client-visible task_control schema does not expose top-level task_context_id, while runtime workspace targeting can require task_context_id or run_id when multiple authorized roots exist. Locate the authoritative ToolSpec/schema and runtime target-resolution path, make the smallest coherent fix so task_control accepts an optional top-level MCP 2026 task_context_id consistently with the other smart-v3 tools and uses it for the existing scoped task/workspace resolution without weakening fail-closed multi-root routing. Preserve run_id/wave_id behavior and keep the smart-v3 public surface at exactly 8 tools. Add focused regression coverage that proves the emitted task_control input schema contains task_context_id and that a read-only task_control action such as observation/get can be targeted by task_context_id when no run_id is supplied, while invalid/unbound contexts still fail closed. Do not reset, clean, revert, edit ledger.sqlite3 directly, or modify unrelated WIP. Do not restart runtime, push, publish, package, release, or deploy. Finish with focused tests and the cheapest affected contract/schema proof.
- Objective revision: `1`
- Objective SHA-256: `ef239baaf0ce6eb445b0916ffe48d7a6be531b22b337a0a77828f42d2c230688`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `148de18795787e820ef1bc51d0f2591052d24238`
- Worktree fingerprint: `7b5c665b05ecb7c417a41c0ccc7046fbcc66c1aca784a0c8ef9f1b31d86ef3b4`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 31484 | 2026-08-28T07:15:57.537Z | run_started |  | PREFLIGHT |  |
| 31485 | 2026-08-28T07:15:58.063Z | observation_span_recorded |  |  |  |
| 31486 | 2026-08-28T07:15:58.281Z | solution_shadow_recommended |  |  |  |
| 31487 | 2026-08-28T07:15:59.353Z | observation_span_recorded |  |  |  |
| 31488 | 2026-08-28T07:15:59.527Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 31489 | 2026-08-28T07:15:59.730Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 31490 | 2026-08-28T07:15:59.927Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 31491 | 2026-08-28T07:16:00.139Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 31492 | 2026-08-28T07:16:00.319Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 31493 | 2026-08-28T07:16:00.504Z | state_transition | READY | ROUTED | reason=route_selected |
| 31494 | 2026-08-28T07:16:00.719Z | observation_span_recorded |  |  |  |
| 31495 | 2026-08-28T07:16:01.235Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=26fc6591dfc74e9ca50ff0317d427d83 |
| 31496 | 2026-08-28T07:16:01.378Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 31497 | 2026-08-28T07:16:01.773Z | observation_span_recorded |  |  |  |
| 31498 | 2026-08-28T07:16:02.060Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=26fc6591dfc74e9ca50ff0317d427d83 |
| 31499 | 2026-08-28T07:16:02.240Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 31500 | 2026-08-28T07:16:02.618Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=026c1139559f43952187850b3a54f0328f7a1fb5d1e10a500d2119bd18898dfb |
| 31501 | 2026-08-28T07:16:02.930Z | managed_process_admitted |  |  | owner=default |
| 31502 | 2026-08-28T07:16:03.214Z | managed_process_started |  |  | owner=default |
| 31503 | 2026-08-28T07:16:57.715Z | managed_process_terminal |  |  | owner=default |
| 31504 | 2026-08-28T07:16:58.165Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=026c1139559f43952187850b3a54f0328f7a1fb5d1e10a500d2119bd18898dfb |
| 31505 | 2026-08-28T07:16:58.420Z | observation_span_recorded |  |  |  |
| 31506 | 2026-08-28T07:16:58.681Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 31507 | 2026-08-28T07:16:58.916Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 31508 | 2026-08-28T07:16:59.170Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 026c1139559f43952187850b3a54f0328f7a1fb5d1e10a500d2119bd18898dfb | False | 55157 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `37`
- Chain head: `205ab39d65430000dc7762ab3b00ffbc39baa9d4c2150a1ba1d84449ea894839`
