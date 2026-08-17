# Orchestration Wave 1

- Run: `18f59868b4164dc0a42e9600a3b5a37b`
- Wave: `87f0749155104aab8c3e609ea481a27b`
- Objective: P1.2 only: define the controlled eligible-run denominator for host-binding coverage from the existing evaluation/host-correlation contract before calculating the metric. The denominator must be rule-based and evidence-calibrated, not chosen to maximize coverage. Determine which run metadata fields prove that a run was eligible for ChatWeb host observation/correlation (for example explicit trace_id/turn_id and any activation/provenance constraints), how legacy pre-activation runs are excluded, and how to compute eligible_runs_total, eligible_runs_with_host_span, eligible_run_host_coverage plus existing span-level binding without timestamp proximity. Identify the smallest implementation/test/report change needed. Do not mutate in prepare; do not solve P1.3 controller usage or P1.4 quality population here.
- Mode: `mcp_only`
- Base HEAD: `db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc`
- Worktree fingerprint: `97f7c04f7a0f7efa3c29986b937e83b885bca83117cb8873b69dd11f8e54a89b`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 14349 | 2026-08-17T15:04:46.762Z | run_started |  | PREFLIGHT |  |
| 14350 | 2026-08-17T15:04:51.727Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 14351 | 2026-08-17T15:06:10.618Z | managed_process_admitted |  |  | owner=default |
| 14352 | 2026-08-17T15:06:10.835Z | managed_process_started |  |  | owner=default |
| 14353 | 2026-08-17T15:06:11.205Z | managed_process_terminal |  |  | owner=default |
| 14354 | 2026-08-17T15:06:36.076Z | managed_process_admitted |  |  | owner=default |
| 14355 | 2026-08-17T15:06:36.298Z | managed_process_started |  |  | owner=default |
| 14356 | 2026-08-17T15:06:36.802Z | managed_process_terminal |  |  | owner=default |
| 14357 | 2026-08-17T15:08:01.321Z | managed_process_admitted |  |  | owner=default |
| 14358 | 2026-08-17T15:08:01.563Z | managed_process_started |  |  | owner=default |
| 14359 | 2026-08-17T15:08:01.929Z | managed_process_terminal |  |  | owner=default |
| 14360 | 2026-08-17T15:08:16.846Z | managed_process_admitted |  |  | owner=default |
| 14361 | 2026-08-17T15:08:17.096Z | managed_process_started |  |  | owner=default |
| 14362 | 2026-08-17T15:08:17.845Z | managed_process_terminal |  |  | owner=default |
| 14363 | 2026-08-17T15:09:10.912Z | managed_process_admitted |  |  | owner=default |
| 14364 | 2026-08-17T15:09:11.113Z | managed_process_started |  |  | owner=default |
| 14365 | 2026-08-17T15:09:11.495Z | managed_process_terminal |  |  | owner=default |
| 14366 | 2026-08-17T15:09:22.935Z | managed_process_admitted |  |  | owner=default |
| 14367 | 2026-08-17T15:09:23.155Z | managed_process_started |  |  | owner=default |
| 14368 | 2026-08-17T15:09:23.486Z | managed_process_terminal |  |  | owner=default |
| 14369 | 2026-08-17T15:09:35.763Z | managed_process_admitted |  |  | owner=default |
| 14370 | 2026-08-17T15:09:35.972Z | managed_process_started |  |  | owner=default |
| 14371 | 2026-08-17T15:09:36.378Z | managed_process_terminal |  |  | owner=default |
| 14372 | 2026-08-17T15:09:46.901Z | managed_process_admitted |  |  | owner=default |
| 14373 | 2026-08-17T15:09:47.150Z | managed_process_started |  |  | owner=default |
| 14374 | 2026-08-17T15:09:47.496Z | managed_process_terminal |  |  | owner=default |
| 14375 | 2026-08-17T15:10:00.368Z | managed_process_admitted |  |  | owner=default |
| 14376 | 2026-08-17T15:10:00.610Z | managed_process_started |  |  | owner=default |
| 14377 | 2026-08-17T15:10:00.959Z | managed_process_terminal |  |  | owner=default |
| 14378 | 2026-08-17T15:10:14.396Z | managed_process_admitted |  |  | owner=default |
| 14379 | 2026-08-17T15:10:14.634Z | managed_process_started |  |  | owner=default |
| 14380 | 2026-08-17T15:10:14.963Z | managed_process_terminal |  |  | owner=default |
| 14381 | 2026-08-17T15:11:48.046Z | managed_process_admitted |  |  | owner=default |
| 14382 | 2026-08-17T15:11:48.229Z | managed_process_started |  |  | owner=default |
| 14383 | 2026-08-17T15:11:48.691Z | managed_process_terminal |  |  | owner=default |
| 14384 | 2026-08-17T15:12:31.046Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 14385 | 2026-08-17T15:12:31.157Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 14386 | 2026-08-17T15:12:31.284Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 14387 | 2026-08-17T15:12:31.428Z | state_transition | READY | ROUTED | reason=route_selected |
| 14388 | 2026-08-17T15:12:32.005Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=5fe3a6a22f9d47619cd9c4119a6868ce |
| 14389 | 2026-08-17T15:12:32.144Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 14390 | 2026-08-17T15:12:32.912Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=5fe3a6a22f9d47619cd9c4119a6868ce |
| 14391 | 2026-08-17T15:12:33.011Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 14392 | 2026-08-17T15:12:33.556Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:f35f8e2de717f34a; input_fingerprint=9f9f0e9c25d3601e1dd1e5603590ccac821977a0c160ac5e3cf64a0cd045928f |
| 14393 | 2026-08-17T15:12:34.072Z | managed_process_admitted |  |  | owner=default |
| 14394 | 2026-08-17T15:12:34.298Z | managed_process_started |  |  | owner=default |
| 14395 | 2026-08-17T15:12:35.640Z | managed_process_terminal |  |  | owner=default |
| 14396 | 2026-08-17T15:12:35.846Z | proof_recorded |  |  | stage_id=check:f35f8e2de717f34a; status=passed; cache_hit=False; input_fingerprint=9f9f0e9c25d3601e1dd1e5603590ccac821977a0c160ac5e3cf64a0cd045928f |
| 14397 | 2026-08-17T15:12:36.466Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 14398 | 2026-08-17T15:12:58.150Z | managed_process_admitted |  |  | owner=default |
| 14399 | 2026-08-17T15:12:58.381Z | managed_process_started |  |  | owner=default |
| 14400 | 2026-08-17T15:12:58.729Z | managed_process_terminal |  |  | owner=default |
| 14401 | 2026-08-17T15:13:23.613Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 14402 | 2026-08-17T15:13:23.949Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:f35f8e2de717f34a | passed | 9f9f0e9c25d3601e1dd1e5603590ccac821977a0c160ac5e3cf64a0cd045928f | False | 1890 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 919f3da563434786847f76524beaca9f | accepted | db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc | 1827c47b87a439a3ac5ad1282add2e8e141100561c253f7f1437e3c74c1593c6 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `54`
- Chain head: `5dbab40bb1573d22a15c4ff53eb931f674c6a2a229ddc46916631e734a989e57`
