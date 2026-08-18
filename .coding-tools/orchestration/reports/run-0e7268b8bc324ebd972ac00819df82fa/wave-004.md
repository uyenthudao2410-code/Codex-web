# Orchestration Wave 4

- Run: `0e7268b8bc324ebd972ac00819df82fa`
- Wave: `6c0de28ef7c1443e81865607266cd767`
- Objective: Audit whether the local checkout actually contains and proves the claimed PR #17 recovery/runtime identity fixes. Verify: main/HEAD and ancestry for f6018a5420c28b5da3e6effc456ee07da25a14ed, a1c664c2, 75169953; dev installation_id derived from canonical running checkout root without persisting raw path; dev A->B takeover with authenticated exact owner_pid+instance_id and descriptor TOCTOU rejection RECOVERY_DESCRIPTOR_CHANGED; legacy missing installation_id stale/bootstrap behavior; packaged fail-closed across installation identities; development startWithWindows forced false and stale dev supervisor suppression via stop.request; runtimeIdentity.js included in Recovery Host fingerprint; workspace settings passed as --workspace and not reused to infer checkout source; authorizedRoots/canonical alias behavior; .coding-tools untouched by the claimed merge. Locate the exact regression tests and authoritative commands. Do not modify files.
- Mode: `mcp_only`
- Base HEAD: `f6018a5420c28b5da3e6effc456ee07da25a14ed`
- Worktree fingerprint: `053fb911f1f100dda64915d6b9743cb7b53e4c18a7f6ee4169acea5ea3e8b3bc`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 16608 | 2026-08-18T08:43:43.756Z | wave_replanned |  | PREFLIGHT | reason=Wave 2 materially narrowed the failure from 3 project failures to one focused ReferenceError. The new exact evidence is that tests/recovery-host.test.js uses RECOVERY_HOST_LEGACY_V1_ADDED_FILE_DIGESTS after the fixture update but its destructuring import did not include that exported constant. The strategy changes to the single missing test import, followed by focused and full repository proof. |
| 16609 | 2026-08-18T08:43:44.261Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 16610 | 2026-08-18T08:43:44.385Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 16611 | 2026-08-18T08:43:44.531Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 16612 | 2026-08-18T08:43:44.671Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 16613 | 2026-08-18T08:43:44.906Z | state_transition | READY | ROUTED | reason=route_selected |
| 16614 | 2026-08-18T08:43:45.412Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3831b309f31148e98f18196979e07cb0 |
| 16615 | 2026-08-18T08:43:45.573Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 16616 | 2026-08-18T08:43:46.220Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3831b309f31148e98f18196979e07cb0 |
| 16617 | 2026-08-18T08:43:46.366Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 16618 | 2026-08-18T08:43:46.870Z | proof_cache_miss |  |  | reason=cold; stage_id=check:863d543d13cf8f9a; input_fingerprint=f6fb45f84bad9155e0b763bfbdff501ea306f536ea1c3c8596bb4d4c126a06c4 |
| 16619 | 2026-08-18T08:43:47.250Z | managed_process_admitted |  |  | owner=default |
| 16620 | 2026-08-18T08:43:47.597Z | managed_process_started |  |  | owner=default |
| 16621 | 2026-08-18T08:43:49.405Z | managed_process_terminal |  |  | owner=default |
| 16622 | 2026-08-18T08:43:49.918Z | proof_recorded |  |  | stage_id=check:863d543d13cf8f9a; status=passed; cache_hit=False; input_fingerprint=f6fb45f84bad9155e0b763bfbdff501ea306f536ea1c3c8596bb4d4c126a06c4 |
| 16623 | 2026-08-18T08:43:50.169Z | proof_cache_miss |  |  | reason=cold; stage_id=check:0f4299d747505d91; input_fingerprint=16e7c00feb14ee497d18b6dbf44bdef9b40f2ba0fa066c6668bca470bd023ee2 |
| 16624 | 2026-08-18T08:43:50.547Z | managed_process_admitted |  |  | owner=default |
| 16625 | 2026-08-18T08:43:50.897Z | managed_process_started |  |  | owner=default |
| 16626 | 2026-08-18T08:43:52.755Z | managed_process_terminal |  |  | owner=default |
| 16627 | 2026-08-18T08:43:53.323Z | proof_recorded |  |  | stage_id=check:0f4299d747505d91; status=passed; cache_hit=False; input_fingerprint=16e7c00feb14ee497d18b6dbf44bdef9b40f2ba0fa066c6668bca470bd023ee2 |
| 16628 | 2026-08-18T08:43:53.540Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=25ed972b317801033cc880cf6f67ce63dd431e54ca42576a5dbb3bbf7cecd54c |
| 16629 | 2026-08-18T08:43:53.945Z | managed_process_admitted |  |  | owner=default |
| 16630 | 2026-08-18T08:43:54.289Z | managed_process_started |  |  | owner=default |
| 16631 | 2026-08-18T08:44:24.656Z | managed_process_terminal |  |  | owner=default |
| 16632 | 2026-08-18T08:44:25.086Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=25ed972b317801033cc880cf6f67ce63dd431e54ca42576a5dbb3bbf7cecd54c |
| 16633 | 2026-08-18T08:44:25.606Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 16634 | 2026-08-18T08:44:38.583Z | managed_process_admitted |  |  | owner=default |
| 16635 | 2026-08-18T08:44:38.955Z | managed_process_started |  |  | owner=default |
| 16636 | 2026-08-18T08:44:39.911Z | managed_process_terminal |  |  | owner=default |
| 16637 | 2026-08-18T08:44:52.995Z | managed_process_admitted |  |  | owner=default |
| 16638 | 2026-08-18T08:44:53.266Z | managed_process_started |  |  | owner=default |
| 16639 | 2026-08-18T08:44:53.723Z | managed_process_terminal |  |  | owner=default |
| 16640 | 2026-08-18T08:45:34.209Z | failure_observed | ACCEPTING | ACCEPTING | reason=Source/test behavior is green, but final status shows resources/coding-tools-mcp/.coding-tools/orchestration/ledger.sqlite3 is a tracked evidence file being deleted. Repository policy requires .coding-tools telemetry/history to remain version-controlled rather than be silently lost. Reject this wave so the exact ledger blob can be relocated under repository-root .coding-tools while keeping the forbidden nested source-state path absent. Then rerun source-bundle and .coding-tools history guards; prior npm test source proof remains otherwise green.; failure_class=SOL_REJECTED |
| 16641 | 2026-08-18T08:45:34.377Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 16642 | 2026-08-18T08:45:34.542Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:863d543d13cf8f9a | passed | f6fb45f84bad9155e0b763bfbdff501ea306f536ea1c3c8596bb4d4c126a06c4 | False | 2719 | 0 |
| check:0f4299d747505d91 | passed | 16e7c00feb14ee497d18b6dbf44bdef9b40f2ba0fa066c6668bca470bd023ee2 | False | 2613 | 0 |
| verify:tests | passed | 25ed972b317801033cc880cf6f67ce63dd431e54ca42576a5dbb3bbf7cecd54c | False | 31155 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `235`
- Chain head: `060ca0a6268d2b3334e7829b2ea9b22a4448f65faa6dd34c3ef57e625695bb94`
