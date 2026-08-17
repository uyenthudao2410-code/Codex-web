# Orchestration Wave 1

- Run: `a0958c27b28f448a8ca244fde8d0def9`
- Wave: `cce1305759c74068bbd83062d453fdcb`
- Objective: P1 Server-First real-process acceptance on Windows for exact product source HEAD 3a3abaff72a8e6382e4c362865becba069e4ecfc. Use the already-proven exact-source webcodex-server and webcodex-runner binaries. First run the maintained PowerShell harness syntax gate, then run the full loopback-only scripts/e2e_server_first_snapshot_ws.ps1 canary. Acceptance is entirely the harness's fail-closed assertions: exact binary identity, two distinct source/compute runners, immutable SourceSnapshot transfer, validation on compute, safe proof identity, no durable raw source, ephemeral checkout cleanup, and unchanged authoritative checkouts. Do not mutate repository source, Git refs, external services, or network resources.
- Mode: `mcp_only`
- Base HEAD: `3a3abaff72a8e6382e4c362865becba069e4ecfc`
- Worktree fingerprint: `2a263a1a22a867df72f56b92122bd173159d571e5e6d55a3646f8f6e0fd22af9`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 10850 | 2026-08-17T02:09:40.455Z | run_started |  | PREFLIGHT |  |
| 10851 | 2026-08-17T02:09:40.853Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 10852 | 2026-08-17T02:09:41.026Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 10853 | 2026-08-17T02:09:41.196Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 10854 | 2026-08-17T02:09:41.378Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 10855 | 2026-08-17T02:09:41.605Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 10856 | 2026-08-17T02:09:41.762Z | state_transition | READY | ROUTED | reason=route_selected |
| 10857 | 2026-08-17T02:09:42.297Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1818231cac91472d8fcdaf7ee9a93030 |
| 10858 | 2026-08-17T02:09:42.445Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 10859 | 2026-08-17T02:09:43.014Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1818231cac91472d8fcdaf7ee9a93030 |
| 10860 | 2026-08-17T02:09:43.212Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 10861 | 2026-08-17T02:09:43.592Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:a4f93051b35478c4; input_fingerprint=311fa44a7403c1639ca34be47dbdf4c3734a50335a14545a093e6cc5ca095555 |
| 10862 | 2026-08-17T02:09:43.866Z | managed_process_admitted |  |  | owner=default |
| 10863 | 2026-08-17T02:09:44.115Z | managed_process_started |  |  | owner=default |
| 10864 | 2026-08-17T02:09:44.685Z | managed_process_terminal |  |  | owner=default |
| 10865 | 2026-08-17T02:09:44.974Z | proof_recorded |  |  | stage_id=check:a4f93051b35478c4; status=passed; cache_hit=False; input_fingerprint=311fa44a7403c1639ca34be47dbdf4c3734a50335a14545a093e6cc5ca095555 |
| 10866 | 2026-08-17T02:09:45.141Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:726c4ad29a752dad; input_fingerprint=003c694abf226565f3cf821fb269ce9cd4209c4a935c2fd40c82552b42c7c9a8 |
| 10867 | 2026-08-17T02:09:45.459Z | managed_process_admitted |  |  | owner=default |
| 10868 | 2026-08-17T02:09:45.723Z | managed_process_started |  |  | owner=default |
| 10869 | 2026-08-17T02:09:46.826Z | managed_process_terminal |  |  | owner=default |
| 10870 | 2026-08-17T02:09:47.063Z | proof_recorded |  |  | stage_id=check:726c4ad29a752dad; status=failed; cache_hit=False; input_fingerprint=003c694abf226565f3cf821fb269ce9cd4209c4a935c2fd40c82552b42c7c9a8 |
| 10871 | 2026-08-17T02:09:47.266Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 10872 | 2026-08-17T02:09:47.396Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 10873 | 2026-08-17T02:09:47.648Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:a4f93051b35478c4 | passed | 311fa44a7403c1639ca34be47dbdf4c3734a50335a14545a093e6cc5ca095555 | False | 1121 | 0 |
| check:726c4ad29a752dad | failed | 003c694abf226565f3cf821fb269ce9cd4209c4a935c2fd40c82552b42c7c9a8 | False | 1610 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `24`
- Chain head: `2ad10a11d826ecba5bd252edf844bc3a6d59a7b0bdc20a82c0f83fbd807e8b01`
