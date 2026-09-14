# Orchestration Wave 2

- Run: `6c5c1ead811b4b919343ef356a0aa704`
- Wave: `081368bfbb1b42fea658c0df5391a512`
- Objective: Continue canonical Problem prl-c76b20e025edfe48b4d18d478d2db09d revision 1 after the first causal patch wave failed only because a broad existing telemetry fixture expected one acceptance span but observed three. Preserve the already-applied two-file projection-reconciliation candidate bytes. Replan verification scope to the exact ghost-projection regression plus existing exact-binding negative controls; do not change unrelated A2 telemetry behavior in this Problem. Confirm the candidate still recovers exact prepared RUN/WAVE only when the projected context is absent/terminal, preserves active foreign-owner fail-closed behavior, records reconciliation, and creates no extra RUN.
- Objective revision: `2`
- Objective SHA-256: `c4bf4f1afc82bb2bb3c127830217302b3b34bd2f74ca0e394ed93ff957e2e0a5`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `ae04947d5969e9ee92bf1fe7532bf30e186f8280`
- Worktree fingerprint: `aeb7cf888c9d263d7c2719672c4aee2de65f9a1c80aa69b5da85a489457c5831`
- Contract fingerprint: `1f8d61854fc8a4c03b5a4a8b772b82a19944bc305947f251da23c7340782c12a`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 53006 | 2026-09-14T05:43:33.081Z | wave_replanned |  | PREFLIGHT | reason=The first implementation wave produced a causal two-file patch, and 10 of 11 tests passed. The sole failure is an existing A2 acceptance-span fixture unrelated to prepared binding. Changed strategy: retain exact candidate bytes and verify only the newly added ghost-projection regression plus existing exact-binding/wrong-binding negative controls, rather than treating unrelated telemetry count drift as a blocker for this Problem. |
| 53007 | 2026-09-14T05:43:33.260Z | observation_span_recorded |  |  |  |
| 53008 | 2026-09-14T05:43:39.013Z | observation_span_recorded |  |  |  |
| 53009 | 2026-09-14T05:43:39.212Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 53010 | 2026-09-14T05:44:29.199Z | managed_process_admitted |  |  | owner=default |
| 53011 | 2026-09-14T05:44:29.524Z | managed_process_started |  |  | owner=default |
| 53012 | 2026-09-14T05:44:30.135Z | managed_process_terminal |  |  | owner=default |
| 53013 | 2026-09-14T05:44:42.261Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 53014 | 2026-09-14T05:44:42.441Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 53015 | 2026-09-14T05:44:42.673Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 53016 | 2026-09-14T05:44:42.851Z | state_transition | READY | ROUTED | reason=route_selected |
| 53017 | 2026-09-14T05:44:43.161Z | observation_span_recorded |  |  |  |
| 53018 | 2026-09-14T05:44:43.715Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=536852fc2c614cc6a5a5e116b4506c33 |
| 53019 | 2026-09-14T05:44:43.873Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 53020 | 2026-09-14T05:44:44.339Z | existing_file_adoption_observed |  |  |  |
| 53021 | 2026-09-14T05:44:44.533Z | observation_span_recorded |  |  |  |
| 53022 | 2026-09-14T05:44:44.781Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=536852fc2c614cc6a5a5e116b4506c33 |
| 53023 | 2026-09-14T05:44:44.938Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 53024 | 2026-09-14T05:44:45.408Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=e75c0af616017bd549ce0e3b2135ef50e2b5b0376ae6b85a70032e084bebc102 |
| 53025 | 2026-09-14T05:44:45.789Z | managed_process_admitted |  |  | owner=default |
| 53026 | 2026-09-14T05:44:46.471Z | managed_process_started |  |  | owner=default |
| 53027 | 2026-09-14T05:45:01.359Z | managed_process_reconciled |  |  | reason=root_process_gone; owner=default |
| 53028 | 2026-09-14T05:45:02.468Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=e75c0af616017bd549ce0e3b2135ef50e2b5b0376ae6b85a70032e084bebc102 |
| 53029 | 2026-09-14T05:45:02.723Z | observation_span_recorded |  |  |  |
| 53030 | 2026-09-14T05:45:02.944Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 53031 | 2026-09-14T05:45:03.182Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 53032 | 2026-09-14T05:46:39.145Z | continuity_telemetry_recorded |  |  |  |
| 53033 | 2026-09-14T05:47:32.781Z | quality_outcome_recorded |  |  |  |
| 53034 | 2026-09-14T05:47:33.013Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 53035 | 2026-09-14T05:47:33.303Z | observation_span_recorded |  |  |  |
| 53036 | 2026-09-14T05:47:33.570Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 53037 | 2026-09-14T05:47:33.802Z | observation_span_recorded |  |  |  |
| 53038 | 2026-09-14T05:47:34.063Z | observation_span_recorded |  |  |  |
| 53039 | 2026-09-14T05:47:34.261Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | e75c0af616017bd549ce0e3b2135ef50e2b5b0376ae6b85a70032e084bebc102 | False | 16688 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 80d45cfe8073423695f86b9c0d520dd8 | accepted | ae04947d5969e9ee92bf1fe7532bf30e186f8280 | bf4fbe4dacbd760f0218dcf6ba3fa94c61677f1d0114a6e8ad3299454fde5e80 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `96`
- Chain head: `c9faf80167567a3929dcc408396646614b29e24976fc944899194364252cbc6b`
