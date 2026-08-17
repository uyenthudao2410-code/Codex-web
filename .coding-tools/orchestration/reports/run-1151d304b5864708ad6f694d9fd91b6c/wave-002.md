# Orchestration Wave 2

- Run: `1151d304b5864708ad6f694d9fd91b6c`
- Wave: `fc5cc270eec8419b93c57e78b2871d0f`
- Objective: Execute P0.2 installed Windows Recovery Supervisor current-session acceptance only on the controlled acceptance installation. Exact source HEAD acaa3582052ab6836ade7b55bd1ff2178ebc5117; exact installer SHA-256 0371F160B33621556F16F537297D60E5575690BE076BE053A5802E2A1532C879; expected installed supervisor SHA-256 E0B906C1EC9AB5C3E9F1F52BA7B3D05F6FEFE42259F15A48AB3077A730076420. Immutable before-state Recovery Host PID 32536 instance 399ea2ec2d751b606a2ffe7788727ac6. Replace only %LOCALAPPDATA%\WebMcpAcceptance-0.3.4, install the same-user Limited WebMCP Recovery Supervisor Scheduled Task from the installed package, prove continuous healthy with the exact same Recovery Host, stop task and prove installed Action Once observes the same host with no spawn, restart and re-prove continuous healthy, prove listener/device coherence, then uninstall the Scheduled Task/supervisor and prove rollback. Never kill or replace the active development Recovery Host/MCP/Tunnel. Do not infer reboot/logon persistence. No source changes and no rebuild.
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
| 12715 | 2026-08-17T08:45:03.138Z | wave_replanned |  | PREFLIGHT | reason=Previous wave stopped because the controlled stale acceptance root remained after an otherwise successful NSIS uninstall. This new wave changes strategy to read-only residue/process diagnosis before any further mutation. |
| 12716 | 2026-08-17T08:45:03.321Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12717 | 2026-08-17T08:45:03.529Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 12718 | 2026-08-17T08:45:03.736Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12719 | 2026-08-17T08:45:03.984Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12720 | 2026-08-17T08:45:04.170Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 12721 | 2026-08-17T08:45:04.313Z | state_transition | READY | ROUTED | reason=route_selected |
| 12722 | 2026-08-17T08:45:04.802Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=5289bf6699fb46c9a6ccfb1b31eeb7cf |
| 12723 | 2026-08-17T08:45:04.944Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12724 | 2026-08-17T08:45:05.520Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=5289bf6699fb46c9a6ccfb1b31eeb7cf |
| 12725 | 2026-08-17T08:45:05.679Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 12726 | 2026-08-17T08:45:06.089Z | proof_cache_miss |  |  | reason=cold; stage_id=check:7edcee32b2e85e67; input_fingerprint=62af6f5cff29e977065ef0d42d1038f4cec290da1de5c3eb0fbeb456cbe16b66 |
| 12727 | 2026-08-17T08:45:06.497Z | managed_process_admitted |  |  | owner=default |
| 12728 | 2026-08-17T08:45:06.795Z | managed_process_started |  |  | owner=default |
| 12729 | 2026-08-17T08:45:08.370Z | managed_process_terminal |  |  | owner=default |
| 12730 | 2026-08-17T08:45:08.694Z | proof_recorded |  |  | stage_id=check:7edcee32b2e85e67; status=passed; cache_hit=False; input_fingerprint=62af6f5cff29e977065ef0d42d1038f4cec290da1de5c3eb0fbeb456cbe16b66 |
| 12731 | 2026-08-17T08:45:08.914Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 12732 | 2026-08-17T08:45:21.155Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 12733 | 2026-08-17T08:45:21.666Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:7edcee32b2e85e67 | passed | 62af6f5cff29e977065ef0d42d1038f4cec290da1de5c3eb0fbeb456cbe16b66 | False | 2248 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 32d85add08a74a33a16265c79d8de68a | accepted | acaa3582052ab6836ade7b55bd1ff2178ebc5117 | 1257c10eb59c8e351a11d939a16dbe4c19d6ce212fac80a9b0681c8d9faf1f7c | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `38`
- Chain head: `fd740e375db743295902c880e2a0c98584398a7287444f946ff9e9168d34c37f`
