# Orchestration Wave 1

- Run: `ddf877ba8b62468092f84160474d5850`
- Wave: `370d597364294cc3a0c94b9e40f87554`
- Objective: Fix the accepted-code auto-activation BASE_HEAD_CHANGED deadlock exposed during Phase 3 deployment. Current controller stores one global baseline.head and throws before discovering a newly accepted checkpoint when Git HEAD has advanced. Replace that with a backward-compatible per-component baseline-head transition: each component baseline row tracks its own head (falling back to legacy baseline.head); when target HEAD differs, compute bounded Git name-only delta from that component's baseline head to current HEAD, union those paths with forced dirty/untracked component paths, and require each current byte to match either the component running-baseline receipt or a canonical accepted receipt on current HEAD. Never recapture changed bytes merely because running_revision==disk_revision. A component may advance its baseline head/revision only after a completed/ALREADY_CURRENT intent whose final revalidation trusted the current HEAD. Components whose bytes/revision are provably unchanged may advance their row head automatically. Keep legacy version-2 state compatible and fail closed on missing/invalid base commit, oversized delta, unaccepted committed changes, or concurrent active intent. Add deterministic regressions for: accepted checkpoint on new HEAD can activate; committed head delta without receipt blocks; already-current externally loaded accepted bytes can safely advance; one component can advance while another remains on old head; and legacy baseline state migrates without trusting new bytes. Preserve Phase 3B source and deployed external supervisor.
- Mode: `mcp_only`
- Base HEAD: `415cb658f43cbd1d2456f65bf5649ed52b87ab25`
- Worktree fingerprint: `d6a56e366b3ef8dc3d27b904e5a8a5f3a79c3f00438f02b7692b2e7a29191566`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 6760 | 2026-08-16T09:18:52.863Z | run_started |  | PREFLIGHT |  |
| 6761 | 2026-08-16T09:18:56.862Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 6762 | 2026-08-16T09:28:23.949Z | managed_process_admitted |  |  | owner=default |
| 6763 | 2026-08-16T09:28:31.124Z | managed_process_started |  |  | owner=default |
| 6764 | 2026-08-16T09:28:36.038Z | managed_process_terminal |  |  | owner=default |
| 6765 | 2026-08-16T09:39:40.176Z | managed_process_admitted |  |  | owner=default |
| 6766 | 2026-08-16T09:39:40.535Z | managed_process_started |  |  | owner=default |
| 6767 | 2026-08-16T09:39:41.018Z | managed_process_terminal |  |  | owner=default |
| 6768 | 2026-08-16T09:41:47.207Z | managed_process_admitted |  |  | owner=default |
| 6769 | 2026-08-16T09:41:47.524Z | managed_process_started |  |  | owner=default |
| 6770 | 2026-08-16T09:41:48.182Z | managed_process_terminal |  |  | owner=default |
| 6771 | 2026-08-16T09:41:57.199Z | managed_process_admitted |  |  | owner=default |
| 6772 | 2026-08-16T09:41:57.441Z | managed_process_started |  |  | owner=default |
| 6773 | 2026-08-16T09:41:57.949Z | managed_process_terminal |  |  | owner=default |
| 6774 | 2026-08-16T09:42:32.532Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 6775 | 2026-08-16T09:42:32.672Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 6776 | 2026-08-16T09:42:32.797Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 6777 | 2026-08-16T09:42:32.913Z | state_transition | READY | ROUTED | reason=route_selected |
| 6778 | 2026-08-16T09:42:33.305Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=72b0851357af44d38c44a7e74383096d |
| 6779 | 2026-08-16T09:42:33.464Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 6780 | 2026-08-16T09:42:33.963Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=72b0851357af44d38c44a7e74383096d |
| 6781 | 2026-08-16T09:42:34.080Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 6782 | 2026-08-16T09:42:34.382Z | proof_cache_miss |  |  | reason=cold; stage_id=check:7461bc5dce821b50; input_fingerprint=9d06953758283781e084a0253ec8c94294cfd328358714417e96b55370787f30 |
| 6783 | 2026-08-16T09:42:34.635Z | managed_process_admitted |  |  | owner=default |
| 6784 | 2026-08-16T09:42:34.855Z | managed_process_started |  |  | owner=default |
| 6785 | 2026-08-16T09:42:35.189Z | managed_process_terminal |  |  | owner=default |
| 6786 | 2026-08-16T09:42:35.505Z | proof_recorded |  |  | stage_id=check:7461bc5dce821b50; status=passed; cache_hit=False; input_fingerprint=9d06953758283781e084a0253ec8c94294cfd328358714417e96b55370787f30 |
| 6787 | 2026-08-16T09:42:35.658Z | proof_cache_miss |  |  | reason=cold; stage_id=check:90447173833573ac; input_fingerprint=2f142e8e40ab38f69574431d5f0e8933a7aca0253fcb7dddb68b8fc741f83151 |
| 6788 | 2026-08-16T09:42:35.889Z | managed_process_admitted |  |  | owner=default |
| 6789 | 2026-08-16T09:42:36.132Z | managed_process_started |  |  | owner=default |
| 6790 | 2026-08-16T09:42:51.889Z | managed_process_terminal |  |  | owner=default |
| 6791 | 2026-08-16T09:42:52.094Z | proof_recorded |  |  | stage_id=check:90447173833573ac; status=passed; cache_hit=False; input_fingerprint=2f142e8e40ab38f69574431d5f0e8933a7aca0253fcb7dddb68b8fc741f83151 |
| 6792 | 2026-08-16T09:42:52.264Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=a2beb80b867ff0afa07c693d88895a6e5f5b00e944b3a5e8ef83831b0f04c358 |
| 6793 | 2026-08-16T09:42:52.481Z | managed_process_admitted |  |  | owner=default |
| 6794 | 2026-08-16T09:42:52.727Z | managed_process_started |  |  | owner=default |
| 6795 | 2026-08-16T09:43:10.715Z | managed_process_terminal |  |  | owner=default |
| 6796 | 2026-08-16T09:43:10.988Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=a2beb80b867ff0afa07c693d88895a6e5f5b00e944b3a5e8ef83831b0f04c358 |
| 6797 | 2026-08-16T09:43:11.123Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 6798 | 2026-08-16T09:43:11.256Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 6799 | 2026-08-16T09:43:11.369Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:7461bc5dce821b50 | passed | 9d06953758283781e084a0253ec8c94294cfd328358714417e96b55370787f30 | False | 843 | 0 |
| check:90447173833573ac | passed | 2f142e8e40ab38f69574431d5f0e8933a7aca0253fcb7dddb68b8fc741f83151 | False | 16217 | 0 |
| verify:tests | failed | a2beb80b867ff0afa07c693d88895a6e5f5b00e944b3a5e8ef83831b0f04c358 | False | 18485 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `70`
- Chain head: `5d67bb76ec16b35e70c723aedb0fca495ce9efc834658c171df14383e8beefbf`
