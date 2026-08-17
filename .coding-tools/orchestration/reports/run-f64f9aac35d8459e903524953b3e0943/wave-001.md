# Orchestration Wave 1

- Run: `f64f9aac35d8459e903524953b3e0943`
- Wave: `855626394161448fa5ea98ed60c61c62`
- Objective: Record only the clean final P0.2 rollback verification. On exact HEAD acaa3582052ab6836ade7b55bd1ff2178ebc5117, verify Recovery Supervisor Scheduled Task is absent, %LOCALAPPDATA%\WebMcpRecoverySupervisor is absent, recovery-supervisor-status.json state is uninstalled, and %LOCALAPPDATA%\WebMcpAcceptance-0.3.4 remains present. Through shipped RecoveryIpcClient.lightweightSnapshot require primary mcpRunning/nativeAlive/tunnelRunning/fullyReady all true, recovery host/mcp/tunnel all healthy, and exact Recovery Host PID 32536 instance 399ea2ec2d751b606a2ffe7788727ac6. Independently require exactly one listener on 18766/18767/18082/18083 with expected source-tree executable families and Recovery /healthz ok. Run no unrelated tests and make no mutation.
- Mode: `mcp_only`
- Base HEAD: `acaa3582052ab6836ade7b55bd1ff2178ebc5117`
- Worktree fingerprint: `d616be680020a4a08fc31fc3faebeb18de79383ed04796edf35604d5e0d7e857`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13008 | 2026-08-17T09:02:42.011Z | run_started |  | PREFLIGHT |  |
| 13009 | 2026-08-17T09:02:42.591Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13010 | 2026-08-17T09:02:42.737Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 13011 | 2026-08-17T09:02:42.920Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13012 | 2026-08-17T09:02:43.106Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13013 | 2026-08-17T09:02:43.370Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 13014 | 2026-08-17T09:02:43.584Z | state_transition | READY | ROUTED | reason=route_selected |
| 13015 | 2026-08-17T09:02:44.168Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=193165903ebb444a969ba1625fefc49f |
| 13016 | 2026-08-17T09:02:44.357Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13017 | 2026-08-17T09:02:45.290Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=193165903ebb444a969ba1625fefc49f |
| 13018 | 2026-08-17T09:02:45.671Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13019 | 2026-08-17T09:02:46.208Z | proof_cache_miss |  |  | reason=cold; stage_id=check:44a9b176ec81a2a8; input_fingerprint=7a004f20807e618c8026eee95bbb3ebac8f34a1c24942314e11f8517c3b2d87b |
| 13020 | 2026-08-17T09:02:46.749Z | managed_process_admitted |  |  | owner=default |
| 13021 | 2026-08-17T09:02:47.104Z | managed_process_started |  |  | owner=default |
| 13022 | 2026-08-17T09:02:49.098Z | managed_process_terminal |  |  | owner=default |
| 13023 | 2026-08-17T09:02:49.591Z | proof_recorded |  |  | stage_id=check:44a9b176ec81a2a8; status=passed; cache_hit=False; input_fingerprint=7a004f20807e618c8026eee95bbb3ebac8f34a1c24942314e11f8517c3b2d87b |
| 13024 | 2026-08-17T09:02:49.811Z | proof_cache_miss |  |  | reason=cold; stage_id=check:0408b23ca6aa7f7b; input_fingerprint=d68b3f6e9953b80d05ce866b0002b7046ae296be415a6f2aa6a7e7e8e6536689 |
| 13025 | 2026-08-17T09:02:50.239Z | managed_process_admitted |  |  | owner=default |
| 13026 | 2026-08-17T09:02:50.640Z | managed_process_started |  |  | owner=default |
| 13027 | 2026-08-17T09:02:51.223Z | managed_process_terminal |  |  | owner=default |
| 13028 | 2026-08-17T09:02:51.603Z | proof_recorded |  |  | stage_id=check:0408b23ca6aa7f7b; status=passed; cache_hit=False; input_fingerprint=d68b3f6e9953b80d05ce866b0002b7046ae296be415a6f2aa6a7e7e8e6536689 |
| 13029 | 2026-08-17T09:02:51.808Z | proof_cache_miss |  |  | reason=cold; stage_id=check:f37183896e16cbe4; input_fingerprint=b511de86182807d922eb215d2e945f4003fc0a3e7bbc46fdb633ccadd7742ee7 |
| 13030 | 2026-08-17T09:02:52.315Z | managed_process_admitted |  |  | owner=default |
| 13031 | 2026-08-17T09:02:52.665Z | managed_process_started |  |  | owner=default |
| 13032 | 2026-08-17T09:02:55.022Z | managed_process_terminal |  |  | owner=default |
| 13033 | 2026-08-17T09:02:55.461Z | proof_recorded |  |  | stage_id=check:f37183896e16cbe4; status=passed; cache_hit=False; input_fingerprint=b511de86182807d922eb215d2e945f4003fc0a3e7bbc46fdb633ccadd7742ee7 |
| 13034 | 2026-08-17T09:02:55.687Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 13035 | 2026-08-17T09:02:59.397Z | managed_process_admitted |  |  | owner=chatweb-compute |
| 13036 | 2026-08-17T09:02:59.747Z | managed_process_started |  |  | owner=chatweb-compute |
| 13037 | 2026-08-17T09:03:00.347Z | managed_process_terminal |  |  | owner=chatweb-compute |
| 13038 | 2026-08-17T09:03:15.662Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 13039 | 2026-08-17T09:03:16.128Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:44a9b176ec81a2a8 | passed | 7a004f20807e618c8026eee95bbb3ebac8f34a1c24942314e11f8517c3b2d87b | False | 2934 | 0 |
| check:0408b23ca6aa7f7b | passed | d68b3f6e9953b80d05ce866b0002b7046ae296be415a6f2aa6a7e7e8e6536689 | False | 1379 | 0 |
| check:f37183896e16cbe4 | passed | b511de86182807d922eb215d2e945f4003fc0a3e7bbc46fdb633ccadd7742ee7 | False | 3185 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 11007e2b3be6411dbffc5d507351b07d | accepted | acaa3582052ab6836ade7b55bd1ff2178ebc5117 | 89ded2b4753bd945a0e83d3d220b8eb1cbb5d9bebc52a9bf97ed7006c34a8329 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `32`
- Chain head: `71520990da4f1e0beb24980513c1bbb7327c01cf9cb680cc3381a070cf959209`
