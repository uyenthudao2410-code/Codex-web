# Orchestration Wave 2

- Run: `c5ffbdee45794fbcb06de3801eb7cef2`
- Wave: `129efbf17d6e4a5c89d781bc9bff0b02`
- Objective: Repair the proof-integrity defect in the active run: managed execution lifecycle states such as quiesced, terminated, timed_out, or otherwise non-success-terminal must never be reduced to PASS merely because the root process exit_code is 0. Preserve existing two Rust test-only changes and all public/runtime policy invariants. Implement the smallest fail-closed status classification at the common proof-result boundary and add focused Python regressions covering at least exited+0 => PASS versus quiesced/terminated/timeout+0 => non-PASS. Do not restart runtime and do not activate P5.
- Objective revision: `2`
- Objective SHA-256: `f7c92831793053ee7fadc974f3f39444b24b032f6b1fc3587a996e81dfac2565`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `9e150020a0c0829a988ffea527d5c8d82132ed65`
- Worktree fingerprint: `7b54aa5ab96a3b29ba50523d4283c0e0553d039c6634fd3c18da1cfeab1344ff`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 28640 | 2026-08-23T04:53:41.974Z | wave_replanned |  | PREFLIGHT | reason=The active proof-integrity run entered REPLAN after its initial pre-write shadow gate. A task-level solution shadow recommendation is already recorded. Continue the same causal objective now: locate the common lifecycle-to-proof reducer, implement one fail-closed repair with focused regressions, and do not touch unrelated routing/runtime behavior. |
| 28641 | 2026-08-23T04:53:42.180Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 28642 | 2026-08-23T04:53:42.371Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 28643 | 2026-08-23T04:53:42.537Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 28644 | 2026-08-23T04:53:42.714Z | state_transition | READY | ROUTED | reason=route_selected |
| 28645 | 2026-08-23T04:53:43.521Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=464646da98f94fb8a238c8d1225bf257 |
| 28646 | 2026-08-23T04:53:43.681Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 28647 | 2026-08-23T04:53:44.441Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=464646da98f94fb8a238c8d1225bf257 |
| 28648 | 2026-08-23T04:53:44.616Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 28649 | 2026-08-23T04:53:45.413Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=b7c8318e21d059f4455e00d69b0dce83ca2aa175bb5f80f3c7a9c41385f5bd97 |
| 28650 | 2026-08-23T04:53:45.781Z | managed_process_admitted |  |  | owner=default |
| 28651 | 2026-08-23T04:53:46.084Z | managed_process_started |  |  | owner=default |
| 28652 | 2026-08-23T04:54:09.473Z | managed_process_terminal |  |  | owner=default |
| 28653 | 2026-08-23T04:54:10.731Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=b7c8318e21d059f4455e00d69b0dce83ca2aa175bb5f80f3c7a9c41385f5bd97 |
| 28654 | 2026-08-23T04:54:10.933Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 28655 | 2026-08-23T06:04:30.365Z | failure_observed | ACCEPTING | ACCEPTING | reason=Final Acceptance rejected: current proof-integrity repair is incomplete. Fresh source review found resources/coding-tools-mcp/coding_tools_mcp/exec_tools.py verify_build runner still classifies status as passed solely when payload.exit_code == 0. A managed execution that terminalizes as quiesced/terminated/timed_out with exit_code 0 can therefore still be reduced to PASS. Existing proof cannot support acceptance. Replan must patch this common build-verification result boundary to use fail-closed command lifecycle success semantics and add a deterministic regression for quiesced+0 => non-PASS while preserving exited+0 => PASS. Do not reuse prior full-Rust proof.; failure_class=SOL_REJECTED |
| 28656 | 2026-08-23T06:04:30.515Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 28657 | 2026-08-23T06:04:30.702Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | b7c8318e21d059f4455e00d69b0dce83ca2aa175bb5f80f3c7a9c41385f5bd97 | False | 24905 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `122`
- Chain head: `f5d5313275888b2939cb1adf69d54d748815afc26313b27cb59e574bd0f3be47`
