# Orchestration Wave 1

- Run: `a5b1f4933d574cc390046a92a60987ae`
- Wave: `3d633befc4e44bd386096509172cfc58`
- Objective: Verify and EOCL-record the already-applied dedicated P0.3 F1/F7/F8 acceptance without mutating any additional files. New F8 evidence is limited to tests/recovery-plane.test.js and tests/runtime-lifecycle.test.js. F1 evidence is the existing real Electron process integration in tests/integration/recovery-host-process.test.js. F7 evidence is the existing live-owner/dead-stale-owner lock test in tests/recovery-host.test.js. Acceptance requires: Recovery Plane rejects a genuinely live foreign or unverified owner with typed errors while leaving the PID alive; RuntimeOrchestrator defers a genuinely live recorded MCP PID when health is unavailable and calls no MCP-only recovery, Tunnel-only recovery, or full restart at the first fail-closed boundary; stale dead Recovery Host lock is reclaimable while live lock owner remains protected; real Electron client kill/reattach preserves Recovery Host runtime ownership. Do not modify production source, renderer/UI files, provider traffic, live production processes, or delivery state.
- Mode: `mcp_only`
- Base HEAD: `885260b404c2c64df1b1afa835963045ac55dbf6`
- Worktree fingerprint: `e5cd0aaa6a177cdf0ce3f7b6b7156c5072a28f69915b149ed37c59db48e0ab75`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13795 | 2026-08-17T11:21:40.036Z | run_started |  | PREFLIGHT |  |
| 13796 | 2026-08-17T11:21:40.921Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13797 | 2026-08-17T11:21:41.338Z | managed_process_admitted |  |  | owner=default |
| 13798 | 2026-08-17T11:21:41.689Z | managed_process_started |  |  | owner=default |
| 13799 | 2026-08-17T11:21:48.913Z | managed_process_terminal |  |  | owner=default |
| 13800 | 2026-08-17T11:21:49.120Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 13801 | 2026-08-17T11:21:49.391Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13802 | 2026-08-17T11:21:49.640Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13803 | 2026-08-17T11:21:49.874Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 13804 | 2026-08-17T11:21:50.057Z | state_transition | READY | ROUTED | reason=route_selected |
| 13805 | 2026-08-17T11:21:50.734Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=614307b4b8ea4a7b89308e397f872f72 |
| 13806 | 2026-08-17T11:21:50.941Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13807 | 2026-08-17T11:21:51.620Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=614307b4b8ea4a7b89308e397f872f72 |
| 13808 | 2026-08-17T11:21:51.752Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13809 | 2026-08-17T11:21:52.437Z | proof_cache_miss |  |  | reason=cold; stage_id=check:eca5fe97091e95e8; input_fingerprint=da96ef89d7f839e6554563ef39b537f72ab3ac79189f0a0cf8899f0acf6bf7d8 |
| 13810 | 2026-08-17T11:21:52.884Z | managed_process_admitted |  |  | owner=default |
| 13811 | 2026-08-17T11:21:53.174Z | managed_process_started |  |  | owner=default |
| 13812 | 2026-08-17T11:21:53.629Z | managed_process_terminal |  |  | owner=default |
| 13813 | 2026-08-17T11:21:54.057Z | proof_recorded |  |  | stage_id=check:eca5fe97091e95e8; status=passed; cache_hit=False; input_fingerprint=da96ef89d7f839e6554563ef39b537f72ab3ac79189f0a0cf8899f0acf6bf7d8 |
| 13814 | 2026-08-17T11:21:54.210Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:d3cd01cc730e34e4; input_fingerprint=c1aa1eceb34dc7eb0a8e83abd5deaf40a1a476ee876464b648bc6ad13c1f7dec |
| 13815 | 2026-08-17T11:21:54.545Z | managed_process_admitted |  |  | owner=default |
| 13816 | 2026-08-17T11:21:54.923Z | managed_process_started |  |  | owner=default |
| 13817 | 2026-08-17T11:21:58.712Z | failure_observed | PROVING | PROVING | reason=A non-terminal wave was recovered outside its original synchronous execution.; failure_class=RUNTIME_RESUME_REQUIRED |
| 13818 | 2026-08-17T11:21:58.891Z | state_transition | PROVING | REPLAN | reason=RUNTIME_RESUME_REQUIRED; failure_class=RUNTIME_RESUME_REQUIRED |
| 13819 | 2026-08-17T11:21:59.061Z | managed_process_terminal |  |  | owner=default |
| 13820 | 2026-08-17T11:21:59.769Z | proof_recorded |  |  | stage_id=check:d3cd01cc730e34e4; status=passed; cache_hit=False; input_fingerprint=c1aa1eceb34dc7eb0a8e83abd5deaf40a1a476ee876464b648bc6ad13c1f7dec |
| 13821 | 2026-08-17T11:21:59.941Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 13822 | 2026-08-17T11:22:00.122Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=e4256b42364a5d8297ef9929ad3a54cda41a0083cad7be0e4049403c6e9dfcad |
| 13823 | 2026-08-17T11:22:00.514Z | failure_observed | PROVING | PROVING | failure_class=EXECUTION_OWNER_INVALID |
| 13824 | 2026-08-17T11:22:00.695Z | state_transition | PROVING | REPLAN | reason=EXECUTION_OWNER_INVALID; failure_class=EXECUTION_OWNER_INVALID |
| 13825 | 2026-08-17T11:22:00.936Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:eca5fe97091e95e8 | passed | da96ef89d7f839e6554563ef39b537f72ab3ac79189f0a0cf8899f0acf6bf7d8 | False | 1235 | 0 |
| check:d3cd01cc730e34e4 | passed | c1aa1eceb34dc7eb0a8e83abd5deaf40a1a476ee876464b648bc6ad13c1f7dec | False | 5142 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `50`
- Chain head: `7a26d59bc6837401dc9a8d119b0ea1d9200e0f339347c52d2f31ef07c8a9883a`
