# Orchestration Wave 1

- Run: `62c3ae7e5b5641729d099365e345db6e`
- Wave: `c4f7035d39394c43b9503cfec53d665c`
- Objective: Investigate the Windows-only flaky teardown observed in tests/live-supervisor-e2e.test.js after the behavior itself passed: removeTempTree rmSync returned EPERM on the temporary webcodex-sup-* directory, then the exact test passed immediately on retry. Determine whether the test cleanup fails to wait for the fake native/tunnel/child process tree or lacks bounded Windows filesystem retry, versus an external antivirus/transient handle. Inspect only this test and helpers it directly uses. Do not mutate product runtime unless there is evidence of a real lifecycle leak.
- Mode: `mcp_only`
- Base HEAD: `24825cd82406a24828aaceec5cb846d0fbaeec1a`
- Worktree fingerprint: `012d9346e3517674b86bba5b05c7e317445a2ba03589a29437e07ba0aba30c03`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 12061 | 2026-08-17T07:32:27.911Z | run_started |  | PREFLIGHT |  |
| 12062 | 2026-08-17T07:32:28.517Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12063 | 2026-08-17T07:33:21.188Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12064 | 2026-08-17T07:33:21.345Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12065 | 2026-08-17T07:33:21.506Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12066 | 2026-08-17T07:33:21.716Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 12067 | 2026-08-17T07:33:21.871Z | state_transition | READY | ROUTED | reason=route_selected |
| 12068 | 2026-08-17T07:33:22.427Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=eede2df2e2394f13adb2b6247df085ce |
| 12069 | 2026-08-17T07:33:22.560Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12070 | 2026-08-17T07:33:23.127Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=eede2df2e2394f13adb2b6247df085ce |
| 12071 | 2026-08-17T07:33:23.319Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 12072 | 2026-08-17T07:33:23.705Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:93e1e7cd211df19c; input_fingerprint=415f47fcbf92b72b7adfa9d22eb00e9047853f14b511015bea740ec4a3497049 |
| 12073 | 2026-08-17T07:33:24.160Z | managed_process_admitted |  |  | owner=default |
| 12074 | 2026-08-17T07:33:24.388Z | managed_process_started |  |  | owner=default |
| 12075 | 2026-08-17T07:33:26.469Z | managed_process_terminal |  |  | owner=default |
| 12076 | 2026-08-17T07:33:26.888Z | proof_recorded |  |  | stage_id=check:93e1e7cd211df19c; status=passed; cache_hit=False; input_fingerprint=415f47fcbf92b72b7adfa9d22eb00e9047853f14b511015bea740ec4a3497049 |
| 12077 | 2026-08-17T07:33:27.058Z | proof_cache_miss |  |  | reason=cold; stage_id=check:f42e997e544c077e; input_fingerprint=853cef8dfb98dc96d4bf32ce48468711a068868317419e707d30b5bde18ca70f |
| 12078 | 2026-08-17T07:33:27.362Z | managed_process_admitted |  |  | owner=default |
| 12079 | 2026-08-17T07:33:27.677Z | managed_process_started |  |  | owner=default |
| 12080 | 2026-08-17T07:33:39.947Z | managed_process_terminal |  |  | owner=default |
| 12081 | 2026-08-17T07:33:40.296Z | proof_recorded |  |  | stage_id=check:f42e997e544c077e; status=passed; cache_hit=False; input_fingerprint=853cef8dfb98dc96d4bf32ce48468711a068868317419e707d30b5bde18ca70f |
| 12082 | 2026-08-17T07:33:40.667Z | proof_cache_miss |  |  | reason=cold; stage_id=check:f19926fc67b4eb66; input_fingerprint=c2876203e6af5926076052320aa40ab54c82ee80c5e0cd66f86f705aa0955584 |
| 12083 | 2026-08-17T07:33:41.029Z | managed_process_admitted |  |  | owner=default |
| 12084 | 2026-08-17T07:33:41.277Z | managed_process_started |  |  | owner=default |
| 12085 | 2026-08-17T07:33:41.794Z | managed_process_terminal |  |  | owner=default |
| 12086 | 2026-08-17T07:33:42.129Z | proof_recorded |  |  | stage_id=check:f19926fc67b4eb66; status=passed; cache_hit=False; input_fingerprint=c2876203e6af5926076052320aa40ab54c82ee80c5e0cd66f86f705aa0955584 |
| 12087 | 2026-08-17T07:33:42.647Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 12088 | 2026-08-17T07:33:52.682Z | managed_process_admitted |  |  | owner=default |
| 12089 | 2026-08-17T07:33:52.953Z | managed_process_started |  |  | owner=default |
| 12090 | 2026-08-17T07:34:13.236Z | managed_process_terminal |  |  | owner=default |
| 12091 | 2026-08-17T07:34:26.238Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 12092 | 2026-08-17T07:34:26.583Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:93e1e7cd211df19c | passed | 415f47fcbf92b72b7adfa9d22eb00e9047853f14b511015bea740ec4a3497049 | False | 2849 | 0 |
| check:f42e997e544c077e | passed | 853cef8dfb98dc96d4bf32ce48468711a068868317419e707d30b5bde18ca70f | False | 12910 | 0 |
| check:f19926fc67b4eb66 | passed | c2876203e6af5926076052320aa40ab54c82ee80c5e0cd66f86f705aa0955584 | False | 1097 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| f3864e10934c45d5a9d4f5037f13bb15 | accepted | 24825cd82406a24828aaceec5cb846d0fbaeec1a | b718963027c04e4eb12b0f4a5c89696e39b2b9a21ebd5a6d3005abdc6e6155ed | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `32`
- Chain head: `5f8071ee5e32eea26f70c3dec8428714875ad89f59290667f99cd26337b9dcb1`
