# Orchestration Wave 1

- Run: `2498e44384ec4f8cac2b1a70d0957349`
- Wave: `f58a41cf2d2a4ff79209eda3e43b83aa`
- Objective: Recovery integration preflight correction: apply only the five intended stashed source/test changes, then make the closed-activation compatibility bootstrap accept only exact managed-tunnel-attested ChatWeb authority. Preserve the pulled recycled-PID repair and all existing READY/workspace fail-closed gates.
- Objective revision: `1`
- Objective SHA-256: `2af8c58ff084c4c9114bedbe2a4d667c128d195593ebe06cf1fa306185ccbe4b`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `573b6ff5a5ff2509288c9656e18fd375f1ab32d3`
- Worktree fingerprint: `438b0046c376c49991f8a8f795bae5b8455bd95b0a577214e67e7cfd79174bdb`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 41199 | 2026-09-06T04:57:32.750Z | run_started |  | PREFLIGHT |  |
| 41200 | 2026-09-06T04:57:33.076Z | observation_span_recorded |  |  |  |
| 41201 | 2026-09-06T04:57:33.271Z | solution_shadow_recommended |  |  |  |
| 41202 | 2026-09-06T04:57:33.456Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 41203 | 2026-09-06T04:57:34.024Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 41204 | 2026-09-06T04:57:34.207Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 41205 | 2026-09-06T04:57:34.358Z | state_transition | READY | ROUTED | reason=route_selected |
| 41206 | 2026-09-06T04:57:34.545Z | observation_span_recorded |  |  |  |
| 41207 | 2026-09-06T04:57:34.981Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=79bb38cd3c904e43a7bc5064676ad5b2 |
| 41208 | 2026-09-06T04:57:35.139Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 41209 | 2026-09-06T04:57:35.691Z | patch_surface_observed |  |  |  |
| 41210 | 2026-09-06T04:57:35.979Z | patch_surface_observed |  |  |  |
| 41211 | 2026-09-06T04:57:36.196Z | observation_span_recorded |  |  |  |
| 41212 | 2026-09-06T04:57:36.476Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=79bb38cd3c904e43a7bc5064676ad5b2 |
| 41213 | 2026-09-06T04:57:36.675Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 41214 | 2026-09-06T04:57:37.366Z | observation_span_recorded |  |  |  |
| 41215 | 2026-09-06T04:57:37.600Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 41222 | 2026-09-06T04:58:24.756Z | managed_process_admitted |  |  | owner=default |
| 41223 | 2026-09-06T04:58:25.042Z | managed_process_started |  |  | owner=default |
| 41224 | 2026-09-06T04:58:29.424Z | managed_process_terminal |  |  | owner=default |
| 41228 | 2026-09-06T04:58:37.846Z | managed_process_admitted |  |  | owner=default |
| 41229 | 2026-09-06T04:58:38.270Z | managed_process_started |  |  | owner=default |
| 41230 | 2026-09-06T04:58:41.467Z | managed_process_terminal |  |  | owner=default |
| 41246 | 2026-09-06T04:58:50.642Z | managed_process_admitted |  |  | owner=default |
| 41247 | 2026-09-06T04:58:51.066Z | managed_process_started |  |  | owner=default |
| 41254 | 2026-09-06T04:59:30.669Z | managed_process_terminal |  |  | owner=default |
| 41255 | 2026-09-06T04:59:37.601Z | managed_process_admitted |  |  | owner=default |
| 41256 | 2026-09-06T04:59:37.902Z | managed_process_started |  |  | owner=default |
| 41257 | 2026-09-06T04:59:38.352Z | managed_process_terminal |  |  | owner=default |
| 41258 | 2026-09-06T05:00:12.342Z | observation_span_recorded |  |  |  |
| 41259 | 2026-09-06T05:00:12.528Z | failure_observed | ACCEPTING | ACCEPTING | reason=ACCEPTANCE_PROOF_REQUIRED: post-write Node 56/56, Python 48/48, and diff-check all passed, but they were terminal-managed evidence rather than canonical EOCL proof records. Preserve the exact current bytes, REPLAN under the same RUN, adopt those bytes by SHA-256, and rerun the smallest sufficient verification through agent_workflow so acceptance has content-addressed proof authority.; failure_class=SOL_REJECTED |
| 41260 | 2026-09-06T05:00:12.709Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 41261 | 2026-09-06T05:00:12.873Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `61`
- Chain head: `afeccf1272fba38cd714bef4a0903a407183d03d5b3825dd93a224decc0d9fe1`
