# Orchestration Wave 3

- Run: `088f7fb2b94647088eaac26b32595372`
- Wave: `197361a2d641496d902736160230a0aa`
- Objective: Fix the observed cross-session agent_workflow task/run objective-binding regression. When agent_workflow is called with an explicit objective for a new material workflow/run, that caller objective must be the canonical run initial objective and wave effective objective. The current/global task projection may be updated to reflect it but must never override it with unrelated prior/concurrent task semantics. Reproduction: explicit Wave A feature objective produced run fd8fad90f9794b0fad39893b58c1a73e whose persisted objective was an unrelated Antigravity port-5260 diagnose task. Preserve task history, existing T1 objective revision/hash/source semantics, smart-v3=8, EOCL authority, and unrelated work. Add deterministic regression proving explicit workflow objective wins despite stale/foreign task projection. Do not implement Wave A in this run.
- Objective revision: `1`
- Objective SHA-256: `93217106634d513b1787fbcc83d32e398f7e98726ae94ae6c4daed7d7d28964c`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `3538c761f174f8f609090b31ef368c064df0a5fc`
- Worktree fingerprint: `f5c6e3a0a95f69553b5bb10e12d06fcccf6cd80f2cee6eec76ce84867626ec6a`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 27084 | 2026-08-22T10:11:00.366Z | wave_replanned |  | PREFLIGHT | reason=Wave 2 provided a real traceback: the objective-fence design is reached, but its call to OrchestrationLedger.wave_objective_provenance used only wave_id while the canonical API requires run_id and wave_id. Wave 3 changes that exact API call and broadens verification to task/workflow, orchestration-control, and engineering-casebook regressions. |
| 27085 | 2026-08-22T10:11:00.573Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 27086 | 2026-08-22T10:11:00.769Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 27087 | 2026-08-22T10:11:00.971Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 27088 | 2026-08-22T10:11:01.191Z | state_transition | READY | ROUTED | reason=route_selected |
| 27089 | 2026-08-22T10:11:02.233Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=2e92f75231f740e39c3bad0512854423 |
| 27090 | 2026-08-22T10:11:02.340Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 27091 | 2026-08-22T10:11:03.114Z | patch_surface_observed |  |  |  |
| 27092 | 2026-08-22T10:11:03.423Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=2e92f75231f740e39c3bad0512854423 |
| 27093 | 2026-08-22T10:11:03.559Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 27094 | 2026-08-22T10:11:04.395Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=53465bf155bed84b29cefb353db1630da2c940cef285aafd5776ee32d44efe5c |
| 27095 | 2026-08-22T10:11:04.775Z | managed_process_admitted |  |  | owner=default |
| 27096 | 2026-08-22T10:11:05.125Z | managed_process_started |  |  | owner=default |
| 27097 | 2026-08-22T10:11:37.976Z | managed_process_terminal |  |  | owner=default |
| 27098 | 2026-08-22T10:11:38.377Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=53465bf155bed84b29cefb353db1630da2c940cef285aafd5776ee32d44efe5c |
| 27099 | 2026-08-22T10:11:38.560Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 27100 | 2026-08-22T10:11:38.693Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 27101 | 2026-08-22T10:11:38.874Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 53465bf155bed84b29cefb353db1630da2c940cef285aafd5776ee32d44efe5c | False | 33594 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `61`
- Chain head: `c57d751a0ab9c7cfbc35b2c82711dac77ab10c2d3e56f49ef0f0fad6d260cef4`
