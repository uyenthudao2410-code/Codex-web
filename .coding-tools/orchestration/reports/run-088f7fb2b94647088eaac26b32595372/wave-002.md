# Orchestration Wave 2

- Run: `088f7fb2b94647088eaac26b32595372`
- Wave: `ec295c12b24f4d2691762345659b36b4`
- Objective: Fix the observed cross-session agent_workflow task/run objective-binding regression. When agent_workflow is called with an explicit objective for a new material workflow/run, that caller objective must be the canonical run initial objective and wave effective objective. The current/global task projection may be updated to reflect it but must never override it with unrelated prior/concurrent task semantics. Reproduction: explicit Wave A feature objective produced run fd8fad90f9794b0fad39893b58c1a73e whose persisted objective was an unrelated Antigravity port-5260 diagnose task. Preserve task history, existing T1 objective revision/hash/source semantics, smart-v3=8, EOCL authority, and unrelated work. Add deterministic regression proving explicit workflow objective wins despite stale/foreign task projection. Do not implement Wave A in this run.
- Objective revision: `1`
- Objective SHA-256: `93217106634d513b1787fbcc83d32e398f7e98726ae94ae6c4daed7d7d28964c`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `3538c761f174f8f609090b31ef368c064df0a5fc`
- Worktree fingerprint: `f5c6e3a0a95f69553b5bb10e12d06fcccf6cd80f2cee6eec76ce84867626ec6a`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 27067 | 2026-08-22T10:09:59.880Z | wave_replanned |  | PREFLIGHT | reason=The source fix already materialized correctly in Wave 1. Verification failed only because pytest was launched from repository root while the target test path is component-relative. Replacement Wave 2 changes only the verification workdir to resources/coding-tools-mcp; no source strategy or patch is retried. |
| 27068 | 2026-08-22T10:10:00.040Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 27069 | 2026-08-22T10:10:00.197Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 27070 | 2026-08-22T10:10:00.340Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 27071 | 2026-08-22T10:10:00.456Z | state_transition | READY | ROUTED | reason=route_selected |
| 27072 | 2026-08-22T10:10:01.510Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f8e0eb5480d0456197c5ce0fb37d58f9 |
| 27073 | 2026-08-22T10:10:01.636Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 27074 | 2026-08-22T10:10:02.806Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f8e0eb5480d0456197c5ce0fb37d58f9 |
| 27075 | 2026-08-22T10:10:03.454Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 27076 | 2026-08-22T10:10:04.815Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=f7f870ca6d13a47e08c97add26bebdc689939b03f972383c83d07b2cfaf218aa |
| 27077 | 2026-08-22T10:10:05.133Z | managed_process_admitted |  |  | owner=default |
| 27078 | 2026-08-22T10:10:05.397Z | managed_process_started |  |  | owner=default |
| 27079 | 2026-08-22T10:10:09.907Z | managed_process_terminal |  |  | owner=default |
| 27080 | 2026-08-22T10:10:10.132Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=f7f870ca6d13a47e08c97add26bebdc689939b03f972383c83d07b2cfaf218aa |
| 27081 | 2026-08-22T10:10:10.248Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 27082 | 2026-08-22T10:10:10.416Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 27083 | 2026-08-22T10:10:10.592Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | f7f870ca6d13a47e08c97add26bebdc689939b03f972383c83d07b2cfaf218aa | False | 5078 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `61`
- Chain head: `c57d751a0ab9c7cfbc35b2c82711dac77ab10c2d3e56f49ef0f0fad6d260cef4`
