# Orchestration Wave 1

- Run: `e10a55eab39c4d9cbfddc37a48b58f8e`
- Wave: `c40ff646a8004a5fbf2382a12603cf28`
- Objective: W3 Provider UsageEvent Hardening: adopt the exact pre-existing W3 source bytes only; prove pricing_revision provenance, attribution status exact/partial/unassigned, provider-reported cost precedence, and exact fixture-to-ledger-to-analytics round trip. Do not alter any file bytes. Preserve unrelated dirty state. No commit/push/release/deploy.
- Objective revision: `1`
- Objective SHA-256: `24eb59d05686da1e48ae74162a51d243762d7cfe2a26a7caebda30f0e3a2a854`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `c52d8fe6c3e03ae24f1cd1553f722a4fe6f2d5e887e4f47b3ad70035ece849e1`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 33698 | 2026-08-31T19:32:47.583Z | run_started |  | PREFLIGHT |  |
| 33699 | 2026-08-31T19:32:47.943Z | observation_span_recorded |  |  |  |
| 33700 | 2026-08-31T19:32:48.150Z | solution_shadow_recommended |  |  |  |
| 33701 | 2026-08-31T19:32:48.885Z | observation_span_recorded |  |  |  |
| 33702 | 2026-08-31T19:32:49.086Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 33703 | 2026-08-31T19:32:49.503Z | managed_process_admitted |  |  | owner=default |
| 33704 | 2026-08-31T19:32:49.896Z | managed_process_started |  |  | owner=default |
| 33705 | 2026-08-31T19:32:50.731Z | managed_process_terminal |  |  | owner=default |
| 33706 | 2026-08-31T19:32:50.993Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 33707 | 2026-08-31T19:32:51.226Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 33708 | 2026-08-31T19:32:51.438Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 33709 | 2026-08-31T19:32:51.657Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 33710 | 2026-08-31T19:32:51.854Z | state_transition | READY | ROUTED | reason=route_selected |
| 33711 | 2026-08-31T19:32:52.042Z | observation_span_recorded |  |  |  |
| 33712 | 2026-08-31T19:32:52.870Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=89f0e972a4ff4d37820d0709fc946f62 |
| 33713 | 2026-08-31T19:32:53.054Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 33714 | 2026-08-31T19:32:53.745Z | existing_file_adoption_observed |  |  |  |
| 33715 | 2026-08-31T19:32:54.030Z | observation_span_recorded |  |  |  |
| 33716 | 2026-08-31T19:32:54.387Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=89f0e972a4ff4d37820d0709fc946f62 |
| 33717 | 2026-08-31T19:32:54.568Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 33718 | 2026-08-31T19:32:55.257Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=d2bc4d7a74a144febdf3b89dbfc26269e1d1409e0a4ae5b5cd736210759026fd |
| 33719 | 2026-08-31T19:32:55.680Z | managed_process_admitted |  |  | owner=default |
| 33720 | 2026-08-31T19:32:56.039Z | managed_process_started |  |  | owner=default |
| 33721 | 2026-08-31T19:32:57.130Z | managed_process_terminal |  |  | owner=default |
| 33722 | 2026-08-31T19:32:58.334Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=d2bc4d7a74a144febdf3b89dbfc26269e1d1409e0a4ae5b5cd736210759026fd |
| 33723 | 2026-08-31T19:32:58.644Z | observation_span_recorded |  |  |  |
| 33724 | 2026-08-31T19:32:58.912Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 33833 | 2026-09-01T00:09:34.709Z | failure_observed | ACCEPTING | ACCEPTING | reason=PROVENANCE_ATTRIBUTION_FAIL_OPEN — build_usage_event accepts attribution_status=exact while run_id, wave_id and delegation_id are all empty; completion report does not prove the required mismatch cases.; failure_class=SOL_REJECTED |
| 33834 | 2026-09-01T00:09:34.911Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 33835 | 2026-09-01T00:09:35.146Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | d2bc4d7a74a144febdf3b89dbfc26269e1d1409e0a4ae5b5cd736210759026fd | False | 2641 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `54`
- Chain head: `100cc2034f3311290fffb3b73256b3f48c639a826531baa7c376f74a97898ca2`
