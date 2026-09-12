# Orchestration Wave 1

- Run: `568a3c9381454689af37320bc1153ee7`
- Wave: `1417524d9a264c6384762ffafb41f708`
- Objective: Converge Recovery Host and Coding MCP component state without source writes by no-patch provenance adoption of the pre-existing dirty subset and exact controller attestation of all 26 current component-file bytes, with fresh deterministic proof covering both runtime components.
- Objective revision: `1`
- Objective SHA-256: `0b16c2b459ba9cb0dea6eca0aae110c7daf0c168b0b52974af2d1b5d129725c8`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `c1cab4fb02990a1430fe0a09bc30714357ae3344c7d25a3365d4f0f2b7e0268d`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 44185 | 2026-09-08T17:40:37.209Z | run_started |  | PREFLIGHT |  |
| 44186 | 2026-09-08T17:40:37.922Z | observation_span_recorded |  |  |  |
| 44187 | 2026-09-08T17:40:38.671Z | observation_span_recorded |  |  |  |
| 44188 | 2026-09-08T17:40:38.836Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 44189 | 2026-09-08T17:40:39.012Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 44190 | 2026-09-08T17:40:39.169Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 44191 | 2026-09-08T17:40:39.337Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 44192 | 2026-09-08T17:40:39.525Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 44193 | 2026-09-08T17:40:39.701Z | state_transition | READY | ROUTED | reason=route_selected |
| 44194 | 2026-09-08T17:40:39.951Z | observation_span_recorded |  |  |  |
| 44195 | 2026-09-08T17:40:40.643Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=11b5eaf61ca544e5ae6e2e7de86ac0c0 |
| 44196 | 2026-09-08T17:40:40.802Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 44197 | 2026-09-08T17:40:41.501Z | existing_file_adoption_observed |  |  |  |
| 44198 | 2026-09-08T17:40:41.710Z | observation_span_recorded |  |  |  |
| 44199 | 2026-09-08T17:40:41.980Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=11b5eaf61ca544e5ae6e2e7de86ac0c0 |
| 44200 | 2026-09-08T17:40:42.122Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 44201 | 2026-09-08T17:40:42.821Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a28d809e2f83fe77; input_fingerprint=bf52d0e65910f175e1b88df28dfa63e3397a8538702f8fef2efc2a8a844f6e58 |
| 44202 | 2026-09-08T17:40:43.135Z | managed_process_admitted |  |  | owner=default |
| 44203 | 2026-09-08T17:40:43.416Z | managed_process_started |  |  | owner=default |
| 44204 | 2026-09-08T17:41:47.098Z | managed_process_terminal |  |  | owner=default |
| 44205 | 2026-09-08T17:41:47.384Z | proof_recorded |  |  | stage_id=check:a28d809e2f83fe77; status=passed; cache_hit=False; input_fingerprint=bf52d0e65910f175e1b88df28dfa63e3397a8538702f8fef2efc2a8a844f6e58 |
| 44206 | 2026-09-08T17:41:47.571Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ffce6415600af993; input_fingerprint=3e625243366f3e87573e9183dfc5c097f17016bee60eab97dc73d0cac8ebc28b |
| 44207 | 2026-09-08T17:41:47.871Z | managed_process_admitted |  |  | owner=default |
| 44208 | 2026-09-08T17:41:48.148Z | managed_process_started |  |  | owner=default |
| 44209 | 2026-09-08T17:50:31.576Z | managed_process_terminal |  |  | owner=default |
| 44210 | 2026-09-08T17:50:31.889Z | proof_recorded |  |  | stage_id=check:ffce6415600af993; status=passed; cache_hit=False; input_fingerprint=3e625243366f3e87573e9183dfc5c097f17016bee60eab97dc73d0cac8ebc28b |
| 44211 | 2026-09-08T17:50:32.086Z | observation_span_recorded |  |  |  |
| 44212 | 2026-09-08T17:50:32.390Z | failure_observed | PROVING | PROVING | failure_class=PROOF_TIMEOUT |
| 44213 | 2026-09-08T17:50:32.812Z | state_transition | PROVING | REPLAN | reason=PROOF_TIMEOUT; failure_class=PROOF_TIMEOUT |
| 44214 | 2026-09-08T17:50:33.223Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 45591 | 2026-09-09T10:48:33.348Z | state_transition | REPLAN | ABORTED | reason=Terminalize this detached historical RUN as ABORTED. Canonical replay shows adopted existing files and recorded passed proofs, but the second managed proof job timed out and runtime explicitly emitted PROOF_TIMEOUT before transition to REPLAN. There is no accepted checkpoint and the wave quiesced. Preserve proof/timeout/adoption evidence; do not promote stale proof to acceptance. |
| 45592 | 2026-09-09T10:48:33.802Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:a28d809e2f83fe77 | passed | bf52d0e65910f175e1b88df28dfa63e3397a8538702f8fef2efc2a8a844f6e58 | False | 64294 | 0 |
| check:ffce6415600af993 | passed | 3e625243366f3e87573e9183dfc5c097f17016bee60eab97dc73d0cac8ebc28b | False | 524049 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `32`
- Chain head: `13d1eeb5c038aac38b950fa06ca586bcf382a000f56e38c7db41c88db5f9f67f`
