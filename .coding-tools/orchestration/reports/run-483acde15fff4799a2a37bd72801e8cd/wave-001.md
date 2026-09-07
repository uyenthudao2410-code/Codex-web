# Orchestration Wave 1

- Run: `483acde15fff4799a2a37bd72801e8cd`
- Wave: `678b6efa32014ad795bf3ae66fec081b`
- Objective: Adopt the exact 4-file patch produced by the previous wave without modifying it, then prove the maintenance restart contract: a full 16-ID exact_stale_runs reason is preserved, malformed batches fail closed, exact-stale supervisor maintenance uses full_clean_refresh with sourceCheckpoint=null, ordinary restart still requires accepted source-checkpoint authority, and existing exact stale reconciliation guards continue to pass.
- Objective revision: `1`
- Objective SHA-256: `333378b6d7d8e585b236e98cc3b53071327e29ce0f848a2b30cd5a90e27fdac1`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `24186fefbdbb9c1dca450ae5e96df167be93c87e`
- Worktree fingerprint: `f0b8a07ea9686b31f0bbfbd16a4a5856cee14960beea3c2319146fe425be2a43`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 43181 | 2026-09-07T08:08:05.127Z | run_started |  | PREFLIGHT |  |
| 43182 | 2026-09-07T08:08:05.449Z | observation_span_recorded |  |  |  |
| 43183 | 2026-09-07T08:08:16.415Z | solution_shadow_recommended |  |  |  |
| 43184 | 2026-09-07T08:08:26.566Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 43185 | 2026-09-07T08:08:26.758Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 43186 | 2026-09-07T08:08:26.901Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 43187 | 2026-09-07T08:08:27.073Z | state_transition | READY | ROUTED | reason=route_selected |
| 43188 | 2026-09-07T08:08:27.229Z | observation_span_recorded |  |  |  |
| 43189 | 2026-09-07T08:08:27.913Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=14231ca5403248a9b3c962e22eb75e88 |
| 43190 | 2026-09-07T08:08:28.074Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 43191 | 2026-09-07T08:08:28.760Z | existing_file_adoption_observed |  |  |  |
| 43192 | 2026-09-07T08:08:28.956Z | observation_span_recorded |  |  |  |
| 43193 | 2026-09-07T08:08:29.193Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=14231ca5403248a9b3c962e22eb75e88 |
| 43194 | 2026-09-07T08:08:29.339Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 43195 | 2026-09-07T08:08:29.984Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:676da3863891edd1; input_fingerprint=a467ab5ceab9bf2e6924227d36ca0706a9ecc56c6de459d3c27167d278e5b39c |
| 43196 | 2026-09-07T08:08:30.317Z | managed_process_admitted |  |  | owner=default |
| 43197 | 2026-09-07T08:08:30.575Z | managed_process_started |  |  | owner=default |
| 43198 | 2026-09-07T08:08:31.003Z | managed_process_terminal |  |  | owner=default |
| 43199 | 2026-09-07T08:08:31.307Z | proof_recorded |  |  | stage_id=check:676da3863891edd1; status=passed; cache_hit=False; input_fingerprint=a467ab5ceab9bf2e6924227d36ca0706a9ecc56c6de459d3c27167d278e5b39c |
| 43200 | 2026-09-07T08:08:31.493Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=9b442f3dd5fc204889b244a4a682f8d84945693ddefd72a7387dae9e0b61df6d |
| 43201 | 2026-09-07T08:08:31.793Z | managed_process_admitted |  |  | owner=default |
| 43202 | 2026-09-07T08:08:32.069Z | managed_process_started |  |  | owner=default |
| 43203 | 2026-09-07T08:08:44.652Z | managed_process_terminal |  |  | owner=default |
| 43204 | 2026-09-07T08:08:52.125Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=9b442f3dd5fc204889b244a4a682f8d84945693ddefd72a7387dae9e0b61df6d |
| 43205 | 2026-09-07T08:08:52.443Z | observation_span_recorded |  |  |  |
| 43206 | 2026-09-07T08:08:52.743Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 43207 | 2026-09-07T08:10:56.603Z | managed_process_admitted |  |  | owner=default |
| 43208 | 2026-09-07T08:10:56.953Z | managed_process_started |  |  | owner=default |
| 43209 | 2026-09-07T08:11:12.803Z | managed_process_terminal |  |  | owner=default |
| 43210 | 2026-09-07T08:11:21.905Z | managed_process_admitted |  |  | owner=default |
| 43211 | 2026-09-07T08:11:22.211Z | managed_process_started |  |  | owner=default |
| 43212 | 2026-09-07T08:11:22.698Z | managed_process_terminal |  |  | owner=default |
| 43213 | 2026-09-07T08:12:49.517Z | quality_outcome_recorded |  |  |  |
| 43214 | 2026-09-07T08:12:49.684Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 43215 | 2026-09-07T08:12:49.915Z | observation_span_recorded |  |  |  |
| 43216 | 2026-09-07T08:12:50.114Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:676da3863891edd1 | passed | a467ab5ceab9bf2e6924227d36ca0706a9ecc56c6de459d3c27167d278e5b39c | False | 1034 | 0 |
| verify:tests | passed | 9b442f3dd5fc204889b244a4a682f8d84945693ddefd72a7387dae9e0b61df6d | False | 20311 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| e94c9e1f27344bc5aad0adac76bd9d47 | accepted | 24186fefbdbb9c1dca450ae5e96df167be93c87e | a1d8df0df98c5672e67671dfd8ad3bf244fb75cf5656f0673c66052c24e9fc74 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `36`
- Chain head: `6495dcedf7bba71796050ebc27848469061d5738deaa9e07b32f14c63869040c`
