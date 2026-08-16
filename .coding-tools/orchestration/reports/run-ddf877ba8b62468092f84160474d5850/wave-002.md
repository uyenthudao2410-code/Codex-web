# Orchestration Wave 2

- Run: `ddf877ba8b62468092f84160474d5850`
- Wave: `83a6d3581d4346219bae76ecd0f6621f`
- Objective: Fix the accepted-code auto-activation BASE_HEAD_CHANGED deadlock exposed during Phase 3 deployment. Current controller stores one global baseline.head and throws before discovering a newly accepted checkpoint when Git HEAD has advanced. Replace that with a backward-compatible per-component baseline-head transition: each component baseline row tracks its own head (falling back to legacy baseline.head); when target HEAD differs, compute bounded Git name-only delta from that component's baseline head to current HEAD, union those paths with forced dirty/untracked component paths, and require each current byte to match either the component running-baseline receipt or a canonical accepted receipt on current HEAD. Never recapture changed bytes merely because running_revision==disk_revision. A component may advance its baseline head/revision only after a completed/ALREADY_CURRENT intent whose final revalidation trusted the current HEAD. Components whose bytes/revision are provably unchanged may advance their row head automatically. Keep legacy version-2 state compatible and fail closed on missing/invalid base commit, oversized delta, unaccepted committed changes, or concurrent active intent. Add deterministic regressions for: accepted checkpoint on new HEAD can activate; committed head delta without receipt blocks; already-current externally loaded accepted bytes can safely advance; one component can advance while another remains on old head; and legacy baseline state migrates without trusting new bytes. Preserve Phase 3B source and deployed external supervisor.
- Mode: `mcp_only`
- Base HEAD: `415cb658f43cbd1d2456f65bf5649ed52b87ab25`
- Worktree fingerprint: `fab5f3a75a62f57ee9ebbf0885ddf767f437cd153972e1e61b04dda363e851d8`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 6800 | 2026-08-16T09:43:44.738Z | wave_replanned |  | PREFLIGHT | reason=The failed broad proof exposed an unrelated Windows temp-directory EBUSY teardown in tests/live-supervisor-e2e.test.js, while the changed controller's focused 13-test oracle passed. No source has changed since that proof. Re-run the isolated flaky boundary and then broad authority once; this is a changed proof strategy, not a retry of the implementation. |
| 6801 | 2026-08-16T09:43:44.862Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 6802 | 2026-08-16T09:43:44.987Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 6803 | 2026-08-16T09:43:45.083Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 6804 | 2026-08-16T09:43:45.187Z | state_transition | READY | ROUTED | reason=route_selected |
| 6805 | 2026-08-16T09:43:45.562Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0458fabd72a64ab5bab112ebc3b91fcd |
| 6806 | 2026-08-16T09:43:45.704Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 6807 | 2026-08-16T09:43:46.054Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0458fabd72a64ab5bab112ebc3b91fcd |
| 6808 | 2026-08-16T09:43:46.149Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 6809 | 2026-08-16T09:43:46.455Z | proof_cache_miss |  |  | reason=cold; stage_id=check:93e1e7cd211df19c; input_fingerprint=36868eae18ec835e4984d8e1ba3f713da79b4d6db7e51400e1498cc8c167bb35 |
| 6810 | 2026-08-16T09:43:46.705Z | managed_process_admitted |  |  | owner=default |
| 6811 | 2026-08-16T09:43:46.929Z | managed_process_started |  |  | owner=default |
| 6812 | 2026-08-16T09:43:49.029Z | managed_process_terminal |  |  | owner=default |
| 6813 | 2026-08-16T09:43:49.246Z | proof_recorded |  |  | stage_id=check:93e1e7cd211df19c; status=passed; cache_hit=False; input_fingerprint=36868eae18ec835e4984d8e1ba3f713da79b4d6db7e51400e1498cc8c167bb35 |
| 6814 | 2026-08-16T09:43:49.369Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:90447173833573ac; input_fingerprint=9e9f91f04d2d11064aa3343f020e511798adac472e8b99fe29097d35b6a6add6 |
| 6815 | 2026-08-16T09:43:49.609Z | managed_process_admitted |  |  | owner=default |
| 6816 | 2026-08-16T09:43:49.802Z | managed_process_started |  |  | owner=default |
| 6817 | 2026-08-16T09:44:05.428Z | managed_process_terminal |  |  | owner=default |
| 6818 | 2026-08-16T09:44:05.654Z | proof_recorded |  |  | stage_id=check:90447173833573ac; status=passed; cache_hit=False; input_fingerprint=9e9f91f04d2d11064aa3343f020e511798adac472e8b99fe29097d35b6a6add6 |
| 6819 | 2026-08-16T09:44:05.777Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=fa0603e572a3a8573ea8fde0cff7bc856712934ef7d923ce939a4aebebef9fd5 |
| 6820 | 2026-08-16T09:44:06.022Z | managed_process_admitted |  |  | owner=default |
| 6821 | 2026-08-16T09:44:06.221Z | managed_process_started |  |  | owner=default |
| 6822 | 2026-08-16T09:44:23.437Z | managed_process_terminal |  |  | owner=default |
| 6823 | 2026-08-16T09:44:23.646Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=fa0603e572a3a8573ea8fde0cff7bc856712934ef7d923ce939a4aebebef9fd5 |
| 6824 | 2026-08-16T09:44:23.756Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 6825 | 2026-08-16T09:44:36.508Z | managed_process_admitted |  |  | owner=default |
| 6826 | 2026-08-16T09:44:36.728Z | managed_process_started |  |  | owner=default |
| 6827 | 2026-08-16T09:44:37.220Z | managed_process_terminal |  |  | owner=default |
| 6828 | 2026-08-16T09:44:49.376Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 6829 | 2026-08-16T09:44:49.667Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:93e1e7cd211df19c | passed | 36868eae18ec835e4984d8e1ba3f713da79b4d6db7e51400e1498cc8c167bb35 | False | 2580 | 0 |
| check:90447173833573ac | passed | 9e9f91f04d2d11064aa3343f020e511798adac472e8b99fe29097d35b6a6add6 | False | 16047 | 0 |
| verify:tests | passed | fa0603e572a3a8573ea8fde0cff7bc856712934ef7d923ce939a4aebebef9fd5 | False | 17671 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| f9e1a3153091460e87bb133b88760e14 | accepted | 415cb658f43cbd1d2456f65bf5649ed52b87ab25 | 84083fd0d91ff3a4a5e3d7de1a9f327a84f9a64674cbacb752fd88fc70a49e50 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `70`
- Chain head: `5d67bb76ec16b35e70c723aedb0fca495ce9efc834658c171df14383e8beefbf`
