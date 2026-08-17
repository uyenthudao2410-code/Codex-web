# Orchestration Wave 1

- Run: `e37776b239db4b3f97521f22a4cbc3c0`
- Wave: `1ca7063d5966422d9d3c6a192a6cba13`
- Objective: Prepare a reusable packaged Recovery acceptance lane based on the just-proven isolated win-unpacked probe. Locate existing Recovery Host launcher/login-argv tests and maintained roadmap/current-state wording that should be updated once the lane is codified. The new lane should build on dist:dir separately, launch packaged --recovery-host with isolated --user-data-dir and temp Recovery ports, verify required packaged resources/device identity/recovery mode/Recovery MCP, run packaged Recovery Supervisor Action Once healthy/live-owner/hash-mismatch cases without installing Scheduled Tasks, clean exact isolated PIDs, and verify production Recovery descriptor identity is unchanged. Do not mutate source in this prepare step.
- Mode: `mcp_only`
- Base HEAD: `f1b38e6ca8d63c2d07357f0fc88aa1631021c6b1`
- Worktree fingerprint: `879d7fab0a8c6ef6824f23191f250b18818d31471a0ed0c17c155eb19e159d6d`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 11972 | 2026-08-17T07:22:21.142Z | run_started |  | PREFLIGHT |  |
| 11973 | 2026-08-17T07:22:28.418Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11974 | 2026-08-17T07:24:52.449Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 11975 | 2026-08-17T07:24:52.630Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 11976 | 2026-08-17T07:24:52.812Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 11977 | 2026-08-17T07:24:52.990Z | state_transition | READY | ROUTED | reason=route_selected |
| 11978 | 2026-08-17T07:24:53.455Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=217f9d481dfe4434aeaee25423f5a489 |
| 11979 | 2026-08-17T07:24:53.620Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 11980 | 2026-08-17T07:24:54.366Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=217f9d481dfe4434aeaee25423f5a489 |
| 11981 | 2026-08-17T07:24:54.504Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 11982 | 2026-08-17T07:24:55.186Z | proof_cache_miss |  |  | reason=cold; stage_id=check:719395034be5a3ca; input_fingerprint=9f312cc798cce0c657c83380395c1f579b1b939886fc129978811c8007258c36 |
| 11983 | 2026-08-17T07:24:55.499Z | managed_process_admitted |  |  | owner=default |
| 11984 | 2026-08-17T07:24:55.799Z | managed_process_started |  |  | owner=default |
| 11985 | 2026-08-17T07:24:56.278Z | managed_process_terminal |  |  | owner=default |
| 11986 | 2026-08-17T07:24:56.655Z | proof_recorded |  |  | stage_id=check:719395034be5a3ca; status=passed; cache_hit=False; input_fingerprint=9f312cc798cce0c657c83380395c1f579b1b939886fc129978811c8007258c36 |
| 11987 | 2026-08-17T07:24:56.832Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:fe3ffbf7aa7a92a6; input_fingerprint=0c17dfac1344a4eb82dbf0659be7dd0fa24374912dd09b05d0accf2692d7b917 |
| 11988 | 2026-08-17T07:24:57.155Z | managed_process_admitted |  |  | owner=default |
| 11989 | 2026-08-17T07:24:57.469Z | managed_process_started |  |  | owner=default |
| 11990 | 2026-08-17T07:25:06.372Z | managed_process_terminal |  |  | owner=default |
| 11991 | 2026-08-17T07:25:06.802Z | proof_recorded |  |  | stage_id=check:fe3ffbf7aa7a92a6; status=passed; cache_hit=False; input_fingerprint=0c17dfac1344a4eb82dbf0659be7dd0fa24374912dd09b05d0accf2692d7b917 |
| 11992 | 2026-08-17T07:25:07.010Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:328e123c63857fd8; input_fingerprint=5c0b4002c38e75409f2a6e31c8ee1a57e67ccef8c4df1f417b273031aa3da61c |
| 11993 | 2026-08-17T07:25:07.440Z | managed_process_admitted |  |  | owner=default |
| 11994 | 2026-08-17T07:25:07.815Z | managed_process_started |  |  | owner=default |
| 11995 | 2026-08-17T07:25:28.211Z | managed_process_terminal |  |  | owner=default |
| 11996 | 2026-08-17T07:25:28.623Z | proof_recorded |  |  | stage_id=check:328e123c63857fd8; status=passed; cache_hit=False; input_fingerprint=5c0b4002c38e75409f2a6e31c8ee1a57e67ccef8c4df1f417b273031aa3da61c |
| 11997 | 2026-08-17T07:25:28.796Z | proof_cache_miss |  |  | reason=cold; stage_id=check:d9988f3fbd02b833; input_fingerprint=957b2a5038b832eb840f73708484322e98778bb10a4014a3b07b0502307c0486 |
| 11998 | 2026-08-17T07:25:29.195Z | managed_process_admitted |  |  | owner=default |
| 11999 | 2026-08-17T07:25:29.486Z | managed_process_started |  |  | owner=default |
| 12000 | 2026-08-17T07:25:43.757Z | managed_process_terminal |  |  | owner=default |
| 12001 | 2026-08-17T07:25:44.132Z | proof_recorded |  |  | stage_id=check:d9988f3fbd02b833; status=passed; cache_hit=False; input_fingerprint=957b2a5038b832eb840f73708484322e98778bb10a4014a3b07b0502307c0486 |
| 12002 | 2026-08-17T07:25:44.306Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=4af2a2ac679f39f02c3562b11cec5d0b652db095311fd2a508091c296d2e691e |
| 12003 | 2026-08-17T07:25:44.603Z | managed_process_admitted |  |  | owner=default |
| 12004 | 2026-08-17T07:25:44.886Z | managed_process_started |  |  | owner=default |
| 12005 | 2026-08-17T07:25:45.796Z | managed_process_terminal |  |  | owner=default |
| 12006 | 2026-08-17T07:25:46.126Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=4af2a2ac679f39f02c3562b11cec5d0b652db095311fd2a508091c296d2e691e |
| 12007 | 2026-08-17T07:25:46.687Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 12008 | 2026-08-17T07:26:01.293Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 12009 | 2026-08-17T07:26:01.590Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:719395034be5a3ca | passed | 9f312cc798cce0c657c83380395c1f579b1b939886fc129978811c8007258c36 | False | 1160 | 0 |
| check:fe3ffbf7aa7a92a6 | passed | 0c17dfac1344a4eb82dbf0659be7dd0fa24374912dd09b05d0accf2692d7b917 | False | 9632 | 0 |
| check:328e123c63857fd8 | passed | 5c0b4002c38e75409f2a6e31c8ee1a57e67ccef8c4df1f417b273031aa3da61c | False | 21285 | 0 |
| check:d9988f3fbd02b833 | passed | 957b2a5038b832eb840f73708484322e98778bb10a4014a3b07b0502307c0486 | False | 14959 | 0 |
| check:466c2f308b48c766 | passed | 4af2a2ac679f39f02c3562b11cec5d0b652db095311fd2a508091c296d2e691e | False | 1519 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| a504fb321f08444d9f4bb82e40991ce7 | accepted | f1b38e6ca8d63c2d07357f0fc88aa1631021c6b1 | c1be83267da82b00423aea993a7b1a9f66d3c065f0594e9931e104e375c85d9f | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `38`
- Chain head: `6cd9f97991254044051482212d63333bd8eb7f7cd948622afdc067e5deeade74`
