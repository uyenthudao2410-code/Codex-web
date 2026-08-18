# Orchestration Wave 3

- Run: `0e7268b8bc324ebd972ac00819df82fa`
- Wave: `77a6002387e743c692c57d8dd4488a7d`
- Objective: Audit whether the local checkout actually contains and proves the claimed PR #17 recovery/runtime identity fixes. Verify: main/HEAD and ancestry for f6018a5420c28b5da3e6effc456ee07da25a14ed, a1c664c2, 75169953; dev installation_id derived from canonical running checkout root without persisting raw path; dev A->B takeover with authenticated exact owner_pid+instance_id and descriptor TOCTOU rejection RECOVERY_DESCRIPTOR_CHANGED; legacy missing installation_id stale/bootstrap behavior; packaged fail-closed across installation identities; development startWithWindows forced false and stale dev supervisor suppression via stop.request; runtimeIdentity.js included in Recovery Host fingerprint; workspace settings passed as --workspace and not reused to infer checkout source; authorizedRoots/canonical alias behavior; .coding-tools untouched by the claimed merge. Locate the exact regression tests and authoritative commands. Do not modify files.
- Mode: `mcp_only`
- Base HEAD: `f6018a5420c28b5da3e6effc456ee07da25a14ed`
- Worktree fingerprint: `b95a78c6c94bc1307af9a80dfddd528b907e8e297f028810b55b1b1a5fca07ed`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 16585 | 2026-08-18T08:42:47.656Z | wave_replanned |  | PREFLIGHT | reason=The previous read-only wave identified new concrete causes: f6018a54 expanded the legacy bridge pinned-file contract to include runtimeIdentity.js but two older test fixtures still materialize only deviceIdentity.js; additionally a stray nested resources/coding-tools-mcp/.coding-tools directory violates the existing source-bundle invariant. The implementation strategy is now a minimal fixture update plus removal of that nested private runtime-state directory, followed by the full project oracle. |
| 16586 | 2026-08-18T08:42:48.364Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 16587 | 2026-08-18T08:42:48.568Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 16588 | 2026-08-18T08:42:48.770Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 16589 | 2026-08-18T08:42:49.200Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 16590 | 2026-08-18T08:42:49.397Z | state_transition | READY | ROUTED | reason=route_selected |
| 16591 | 2026-08-18T08:42:49.903Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c01521dfa27b464db34aa187545c3dcc |
| 16592 | 2026-08-18T08:42:50.081Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 16593 | 2026-08-18T08:42:50.903Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c01521dfa27b464db34aa187545c3dcc |
| 16594 | 2026-08-18T08:42:51.102Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 16595 | 2026-08-18T08:42:51.534Z | proof_cache_miss |  |  | reason=cold; stage_id=check:e9e4dcacaa127d4e; input_fingerprint=39f60ec46d632c15d052d174170ada7392bedd97171354ce5cd71908e20df7f6 |
| 16596 | 2026-08-18T08:42:52.105Z | managed_process_admitted |  |  | owner=default |
| 16597 | 2026-08-18T08:42:52.405Z | managed_process_started |  |  | owner=default |
| 16598 | 2026-08-18T08:42:53.717Z | managed_process_terminal |  |  | owner=default |
| 16599 | 2026-08-18T08:42:54.047Z | proof_recorded |  |  | stage_id=check:e9e4dcacaa127d4e; status=passed; cache_hit=False; input_fingerprint=39f60ec46d632c15d052d174170ada7392bedd97171354ce5cd71908e20df7f6 |
| 16600 | 2026-08-18T08:42:54.273Z | proof_cache_miss |  |  | reason=cold; stage_id=check:863d543d13cf8f9a; input_fingerprint=93749d7a4052577144c9d2dbb5e7f51ea5bd7b8b1bd58a89ffcd31ecaeb8937a |
| 16601 | 2026-08-18T08:42:54.641Z | managed_process_admitted |  |  | owner=default |
| 16602 | 2026-08-18T08:42:54.964Z | managed_process_started |  |  | owner=default |
| 16603 | 2026-08-18T08:42:56.397Z | managed_process_terminal |  |  | owner=default |
| 16604 | 2026-08-18T08:42:56.706Z | proof_recorded |  |  | stage_id=check:863d543d13cf8f9a; status=failed; cache_hit=False; input_fingerprint=93749d7a4052577144c9d2dbb5e7f51ea5bd7b8b1bd58a89ffcd31ecaeb8937a |
| 16605 | 2026-08-18T08:42:56.880Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 16606 | 2026-08-18T08:42:57.085Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 16607 | 2026-08-18T08:42:57.297Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:e9e4dcacaa127d4e | passed | 39f60ec46d632c15d052d174170ada7392bedd97171354ce5cd71908e20df7f6 | False | 1949 | 0 |
| check:863d543d13cf8f9a | failed | 93749d7a4052577144c9d2dbb5e7f51ea5bd7b8b1bd58a89ffcd31ecaeb8937a | False | 2082 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `235`
- Chain head: `060ca0a6268d2b3334e7829b2ea9b22a4448f65faa6dd34c3ef57e625695bb94`
