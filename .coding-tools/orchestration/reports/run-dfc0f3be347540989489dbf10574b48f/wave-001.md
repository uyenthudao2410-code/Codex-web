# Orchestration Wave 1

- Run: `dfc0f3be347540989489dbf10574b48f`
- Wave: `9406a7adde4b4fadb459237cd6fba1ce`
- Objective: Perform only the controlled fresh acceptance installation step for P0.2. Preconditions: exact HEAD acaa3582052ab6836ade7b55bd1ff2178ebc5117, exact installer SHA-256 0371F160B33621556F16F537297D60E5575690BE076BE053A5802E2A1532C879, Recovery Host PID 32536 instance 399ea2ec2d751b606a2ffe7788727ac6, no Recovery Supervisor task/root. The stale %LOCALAPPDATA%\WebMcpAcceptance-0.3.4 root may be removed only if it is still empty and has no process under it. Install fresh package there, verify installed supervisor SHA-256 E0B906C1EC9AB5C3E9F1F52BA7B3D05F6FEFE42259F15A48AB3077A730076420, then close only any app processes launched from that acceptance root. Do not register the Scheduled Task yet and do not touch development runtime owners.
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
| 12734 | 2026-08-17T08:46:02.939Z | run_started |  | PREFLIGHT |  |
| 12735 | 2026-08-17T08:46:03.369Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12736 | 2026-08-17T08:46:03.562Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 12737 | 2026-08-17T08:46:03.961Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12738 | 2026-08-17T08:46:04.145Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12739 | 2026-08-17T08:46:04.320Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 12740 | 2026-08-17T08:46:04.507Z | state_transition | READY | ROUTED | reason=route_selected |
| 12741 | 2026-08-17T08:46:04.962Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7df191d805964331a23b191e75f64992 |
| 12742 | 2026-08-17T08:46:05.128Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12743 | 2026-08-17T08:46:05.631Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7df191d805964331a23b191e75f64992 |
| 12744 | 2026-08-17T08:46:05.811Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 12745 | 2026-08-17T08:46:06.231Z | proof_cache_miss |  |  | reason=cold; stage_id=check:b34c15451d2f3eee; input_fingerprint=d3d605b01097a43cbbc71bccad42bf0bbf571857105bed9c779fdafe7ab7a4d7 |
| 12746 | 2026-08-17T08:46:06.555Z | managed_process_admitted |  |  | owner=default |
| 12747 | 2026-08-17T08:46:06.846Z | managed_process_started |  |  | owner=default |
| 12748 | 2026-08-17T08:46:23.038Z | managed_process_terminal |  |  | owner=default |
| 12749 | 2026-08-17T08:46:23.423Z | proof_recorded |  |  | stage_id=check:b34c15451d2f3eee; status=passed; cache_hit=False; input_fingerprint=d3d605b01097a43cbbc71bccad42bf0bbf571857105bed9c779fdafe7ab7a4d7 |
| 12750 | 2026-08-17T08:46:23.634Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 12751 | 2026-08-17T08:46:36.409Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 12752 | 2026-08-17T08:46:36.810Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:b34c15451d2f3eee | passed | d3d605b01097a43cbbc71bccad42bf0bbf571857105bed9c779fdafe7ab7a4d7 | False | 16812 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| de0d75ace1e84bf680fd40299f78efb3 | accepted | acaa3582052ab6836ade7b55bd1ff2178ebc5117 | d301b82c83cf07bd44b5a54ed570c502dd174bd8ae81d1162e52008f597e99dd | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `19`
- Chain head: `f256410ae7978cbb267a2240fbd05d665a2678ed35c470d907288804f7fdb55a`
