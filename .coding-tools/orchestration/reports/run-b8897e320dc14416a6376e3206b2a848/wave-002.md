# Orchestration Wave 2

- Run: `b8897e320dc14416a6376e3206b2a848`
- Wave: `ecca6af7c43e418987dbfb9cd7d072f5`
- Objective: Natural #19 Wave 2 diagnosis only: identify the exact 12 PERMISSION_REQUIRED and 1 PROTECTED_PATH_WRITE failure events that belong to the current accepted_representative_chatweb_mcp_model_free P2 cohort, then inspect only their durable typed payloads and subsequent wave/replan evidence. Determine which are legitimate policy enforcement, which are avoidable request/scope corrections, and which remain observability-unknown. No source or ledger mutation.
- Objective revision: `2`
- Objective SHA-256: `82b6fdb4d0e0027f7564de1aa964bc28892c35a2016e4e6a7bf2a34973fd9cfd`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `1e78fe9b5a4abac5845c3450fee92ce4c4af2bbdd99b513742399b8c4bcef1fa`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 47016 | 2026-09-10T07:20:38.425Z | wave_replanned |  | PREFLIGHT | reason=Wave 1 aggregate evidence was insufficient. Wave 2 changes strategy to inspect the reporter's exact accepted-cohort filtering and the durable event rows needed to identify the 13 cohort occurrences and their typed next-wave evidence, without inferring from global history. |
| 47017 | 2026-09-10T07:20:38.664Z | observation_span_recorded |  |  |  |
| 47018 | 2026-09-10T07:20:46.133Z | observation_span_recorded |  |  |  |
| 47019 | 2026-09-10T07:20:46.353Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 47020 | 2026-09-10T07:23:11.237Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 47021 | 2026-09-10T07:23:11.422Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 47022 | 2026-09-10T07:23:11.823Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 47023 | 2026-09-10T07:23:12.008Z | state_transition | READY | ROUTED | reason=route_selected |
| 47024 | 2026-09-10T07:23:12.508Z | observation_span_recorded |  |  |  |
| 47025 | 2026-09-10T07:23:13.494Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=8140de6364174297a8b4e7441718f62c |
| 47026 | 2026-09-10T07:23:13.719Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 47027 | 2026-09-10T07:23:14.688Z | observation_span_recorded |  |  |  |
| 47028 | 2026-09-10T07:23:15.033Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=8140de6364174297a8b4e7441718f62c |
| 47029 | 2026-09-10T07:23:15.228Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 47030 | 2026-09-10T07:23:16.207Z | proof_cache_miss |  |  | reason=cold; stage_id=check:742473a6802db5da; input_fingerprint=9a8a729e3d648e92f648006a0a1f23fbbaf44923df2fc693b0fd1f451d7827cc |
| 47031 | 2026-09-10T07:23:16.571Z | managed_process_admitted |  |  | owner=default |
| 47032 | 2026-09-10T07:23:16.940Z | managed_process_started |  |  | owner=default |
| 47033 | 2026-09-10T07:23:17.388Z | managed_process_terminal |  |  | owner=default |
| 47034 | 2026-09-10T07:23:17.701Z | proof_recorded |  |  | stage_id=check:742473a6802db5da; status=failed; cache_hit=False; input_fingerprint=9a8a729e3d648e92f648006a0a1f23fbbaf44923df2fc693b0fd1f451d7827cc |
| 47035 | 2026-09-10T07:23:17.853Z | observation_span_recorded |  |  |  |
| 47036 | 2026-09-10T07:23:18.029Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 47037 | 2026-09-10T07:23:18.188Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 47038 | 2026-09-10T07:23:18.422Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:742473a6802db5da | failed | 9a8a729e3d648e92f648006a0a1f23fbbaf44923df2fc693b0fd1f451d7827cc | False | 1179 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `146`
- Chain head: `3a25b061be5f24c8d9aa63c4619f4995991feb539b8703037a9e80b721b28a34`
