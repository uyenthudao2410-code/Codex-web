# Orchestration Wave 1

- Run: `6c59a857595a410d80eed85a343d58da`
- Wave: `ffe24d8791a14e9b9b600f33f46abe62`
- Objective: Implement the prepared token-first basic-user Overview on the current exact E:\DEV\Codex-web worktree. Preserve all telemetry/state/schema and technical DOM bindings, but remove technical/runtime/orchestration detail from the default Overview presentation. Make the six primary KPIs Total Token, Input Token, Output Token, Equivalent Cost, Cached Token, and Token per Accepted Result using canonical measured UsageEvent data and accepted-result counts. Preserve unknown_not_zero semantics and never fabricate controller tokens. Add a compact plain-language measurement strip: execution/provider measured status, ChatWeb controller receipt/estimation status, and estimate confidence status. Keep token trend, token-by-model, cost-by-model, heatmap, and summary visible. Hide runtime source, goal continuity, event ticker, accepted-result technical table, measurement coverage, realtime latency/anomaly cards, restart button, and bottom proof/operator technical grid on default Overview via presentation CSS only; underlying IDs/data remain. Simplify the visible model table to its first four token-centric columns via CSS without deleting technical cells. Do not modify backend accounting, restart runtime, commit, push, release, or deploy.
- Objective revision: `1`
- Objective SHA-256: `ae9f24ba5fb3178c99376500038e5a808a71b660c101c6135026a4ae9e8ef633`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `1eee4e6c31f3684c3636c8e466b5db4b248f623ff33e1180e9771b6e8c8f47fa`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 39122 | 2026-09-04T00:00:16.673Z | run_started |  | PREFLIGHT |  |
| 39123 | 2026-09-04T00:00:17.120Z | observation_span_recorded |  |  |  |
| 39124 | 2026-09-04T00:00:17.373Z | solution_shadow_recommended |  |  |  |
| 39125 | 2026-09-04T00:00:17.637Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 39126 | 2026-09-04T00:00:18.138Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 39127 | 2026-09-04T00:00:18.400Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 39128 | 2026-09-04T00:00:18.621Z | state_transition | READY | ROUTED | reason=route_selected |
| 39129 | 2026-09-04T00:00:18.953Z | observation_span_recorded |  |  |  |
| 39130 | 2026-09-04T00:00:20.157Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=6978d8980e404a67a33d775fd86ceb3a |
| 39131 | 2026-09-04T00:00:20.447Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 39132 | 2026-09-04T00:00:21.728Z | patch_surface_observed |  |  |  |
| 39133 | 2026-09-04T00:00:22.073Z | patch_surface_observed |  |  |  |
| 39134 | 2026-09-04T00:00:22.356Z | patch_surface_observed |  |  |  |
| 39135 | 2026-09-04T00:00:22.650Z | patch_surface_observed |  |  |  |
| 39136 | 2026-09-04T00:00:22.875Z | observation_span_recorded |  |  |  |
| 39137 | 2026-09-04T00:00:23.208Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=6978d8980e404a67a33d775fd86ceb3a |
| 39138 | 2026-09-04T00:00:23.426Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 39139 | 2026-09-04T00:00:24.482Z | proof_cache_miss |  |  | reason=cold; stage_id=check:c5c8750b31bcad7d; input_fingerprint=42fbfe26018ab68f7bf36c9b49e995270f447a8f74be477da13e714c75bbac45 |
| 39140 | 2026-09-04T00:00:24.959Z | managed_process_admitted |  |  | owner=default |
| 39141 | 2026-09-04T00:00:25.303Z | managed_process_started |  |  | owner=default |
| 39142 | 2026-09-04T00:00:25.880Z | managed_process_terminal |  |  | owner=default |
| 39143 | 2026-09-04T00:00:26.383Z | proof_recorded |  |  | stage_id=check:c5c8750b31bcad7d; status=passed; cache_hit=False; input_fingerprint=42fbfe26018ab68f7bf36c9b49e995270f447a8f74be477da13e714c75bbac45 |
| 39144 | 2026-09-04T00:00:26.591Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=b84b9947770fe51217012db66dda2580e0affd4b4850e98ef742be5a71df9409 |
| 39145 | 2026-09-04T00:00:27.127Z | managed_process_admitted |  |  | owner=default |
| 39146 | 2026-09-04T00:00:27.580Z | managed_process_started |  |  | owner=default |
| 39147 | 2026-09-04T00:00:30.219Z | managed_process_terminal |  |  | owner=default |
| 39148 | 2026-09-04T00:00:34.595Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=b84b9947770fe51217012db66dda2580e0affd4b4850e98ef742be5a71df9409 |
| 39149 | 2026-09-04T00:00:36.107Z | observation_span_recorded |  |  |  |
| 39150 | 2026-09-04T00:00:36.348Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 39151 | 2026-09-04T00:01:41.577Z | managed_process_admitted |  |  | owner=chatweb-token-dashboard-accept |
| 39152 | 2026-09-04T00:01:41.979Z | managed_process_started |  |  | owner=chatweb-token-dashboard-accept |
| 39153 | 2026-09-04T00:01:42.719Z | managed_process_terminal |  |  | owner=chatweb-token-dashboard-accept |
| 39154 | 2026-09-04T00:01:50.727Z | quality_outcome_recorded |  |  |  |
| 39155 | 2026-09-04T00:01:50.955Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 39156 | 2026-09-04T00:01:51.258Z | observation_span_recorded |  |  |  |
| 39157 | 2026-09-04T00:01:51.556Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:c5c8750b31bcad7d | passed | 42fbfe26018ab68f7bf36c9b49e995270f447a8f74be477da13e714c75bbac45 | False | 1423 | 0 |
| verify:tests | passed | b84b9947770fe51217012db66dda2580e0affd4b4850e98ef742be5a71df9409 | False | 7125 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 1ac6fb37284140229807f6ddf18acc44 | accepted | 80aceb583202ad381c25687969fb48adbf74622c | f589291f94f9007e361a1073473ff6c3002906f63f5e6288d52c11cfe1060bcb | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `36`
- Chain head: `abd98fcbd5cf1342846b7aab583061d69d253f575b0a02f3c2ef619fa7a1072f`
