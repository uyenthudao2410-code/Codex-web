# Orchestration Wave 2

- Run: `c939fa550f344c94b4f30352fe2cefe4`
- Wave: `148aed32b3c541fcbe66a38fbf114e22`
- Objective: C01/M02 host-side packaged installation acceptance using the already accepted installer and packaged Recovery Supervisor identities. Execute the silent NSIS install from real Windows Task Scheduler host context into E:\WebMcpAcceptanceHost-1.0.0, prove host visibility and exact supervisor bytes, install packaged Recovery Supervisor from that host-visible root, then prove exact manifest, executable hash, healthy capability-bearing supervisor with live PID, unchanged Recovery Host PID+instance, and correct supervisor scheduled task. Fail closed before reboot on any mismatch. No source edit, reboot, commit, push, release, publish, or deploy.
- Objective revision: `2`
- Objective SHA-256: `c50921c0323e8856bf595700bc2163e0c4000f6aa085811b25bf236627d24ddd`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `c6196f257d78c5227226197e2fe498a6e65c61f4928cfeb80cc92145fbc5289f`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 59546 | 2026-09-15T10:41:58.340Z | wave_replanned |  | PREFLIGHT | reason=Previous wave failed before execution because the inline PowerShell command was rejected by the harness with No closing quotation. Strategy changed materially: run the same bounded host-install and verification logic as a UTF-16LE PowerShell EncodedCommand, eliminating nested shell quoting while preserving the exact installer identity, host root, Supervisor identity, and fail-closed probes. |
| 59547 | 2026-09-15T10:41:58.664Z | observation_span_recorded |  |  |  |
| 59548 | 2026-09-15T10:41:59.675Z | observation_span_recorded |  |  |  |
| 59549 | 2026-09-15T10:41:59.864Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 59550 | 2026-09-15T10:42:00.031Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 59551 | 2026-09-15T10:42:00.168Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 59552 | 2026-09-15T10:42:00.360Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 59553 | 2026-09-15T10:42:00.567Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 59554 | 2026-09-15T10:42:00.751Z | state_transition | READY | ROUTED | reason=route_selected |
| 59555 | 2026-09-15T10:42:00.981Z | observation_span_recorded |  |  |  |
| 59556 | 2026-09-15T10:42:01.982Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1022f4df73e740d596858fd491c7636e |
| 59557 | 2026-09-15T10:42:02.200Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 59558 | 2026-09-15T10:42:03.136Z | observation_span_recorded |  |  |  |
| 59559 | 2026-09-15T10:42:03.433Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1022f4df73e740d596858fd491c7636e |
| 59560 | 2026-09-15T10:42:03.614Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 59561 | 2026-09-15T10:42:04.482Z | proof_cache_miss |  |  | reason=cold; stage_id=check:f4c250923f8b7d62; input_fingerprint=187ee717dcd22b0fb8440b3903a60e14f561127a470070f566fee1aee44192cd |
| 59562 | 2026-09-15T10:42:04.871Z | managed_process_admitted |  |  | owner=default |
| 59563 | 2026-09-15T10:42:05.204Z | managed_process_started |  |  | owner=default |
| 59564 | 2026-09-15T10:42:05.599Z | managed_process_terminal |  |  | owner=default |
| 59565 | 2026-09-15T10:42:06.107Z | proof_recorded |  |  | stage_id=check:f4c250923f8b7d62; status=failed; cache_hit=False; input_fingerprint=187ee717dcd22b0fb8440b3903a60e14f561127a470070f566fee1aee44192cd |
| 59566 | 2026-09-15T10:42:06.407Z | observation_span_recorded |  |  |  |
| 59567 | 2026-09-15T10:42:06.599Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 59568 | 2026-09-15T10:42:06.783Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 59569 | 2026-09-15T10:42:07.044Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:f4c250923f8b7d62 | failed | 187ee717dcd22b0fb8440b3903a60e14f561127a470070f566fee1aee44192cd | False | 1107 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `44`
- Chain head: `8092f99f4f279fdfe4e7d4e31456ebc6d0f781bb7fac331d1322305d573acfa9`
