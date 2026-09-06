# Orchestration Wave 2

- Run: `4135fb1a2afd49c787a8fa7f0dd87cb0`
- Wave: `a7a187e643f04d6987eef151b0645c96`
- Objective: REPORT-PARTIAL-01: inspect only the operator completion report builder and its isolation tests to design a bounded report-projection correction for durable canonical patch_surface_observed events after partial apply. Preserve the existing endpoint-test patch as unaccepted and make no source changes in prepare.
- Objective revision: `2`
- Objective SHA-256: `9cee3a724920de4a10c9a96aaf5ea55bad71fd6a9b6d0a7efaadcb7b23d32423`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `8697ace8204e7e3da55d250d4a52d9b2b930116c`
- Worktree fingerprint: `2f4958b6f7a086feb54c7ba127fdef2e0efd37a22de2014389c21af354c7d08f`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 40343 | 2026-09-05T05:51:11.926Z | wave_replanned |  | PREFLIGHT | reason=Changed-scope REPORT-PARTIAL-01 repair after the acknowledged prior endpoint-test REPLAN: durable canonical event seq 40334 proves a content-free applied patch surface while the completion report projects what_changed.files empty. This prepare only reads the two allowed report/test files; it does not retry endpoint adoption/proof or G1 inventory. |
| 40344 | 2026-09-05T05:51:12.107Z | observation_span_recorded |  |  |  |
| 40345 | 2026-09-05T05:51:30.040Z | observation_span_recorded |  |  |  |
| 40346 | 2026-09-05T05:51:30.214Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 40347 | 2026-09-05T05:54:34.420Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 40348 | 2026-09-05T05:54:34.647Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 40349 | 2026-09-05T05:54:34.864Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 40350 | 2026-09-05T05:54:35.053Z | state_transition | READY | ROUTED | reason=route_selected |
| 40351 | 2026-09-05T05:54:35.299Z | observation_span_recorded |  |  |  |
| 40352 | 2026-09-05T05:54:35.847Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e0b4c4e5afa5483689bde82464643950 |
| 40353 | 2026-09-05T05:54:36.082Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 40354 | 2026-09-05T05:54:36.831Z | patch_surface_observed |  |  |  |
| 40355 | 2026-09-05T05:54:37.033Z | observation_span_recorded |  |  |  |
| 40356 | 2026-09-05T05:54:37.314Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e0b4c4e5afa5483689bde82464643950 |
| 40357 | 2026-09-05T05:54:37.512Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 40358 | 2026-09-05T05:54:38.002Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=3a8ef9bf9fbf250639966eacb5fedb15ee3165eed484540e7280d2129e30e822 |
| 40359 | 2026-09-05T05:54:38.408Z | managed_process_admitted |  |  | owner=default |
| 40360 | 2026-09-05T05:54:38.701Z | managed_process_started |  |  | owner=default |
| 40361 | 2026-09-05T05:54:51.988Z | managed_process_terminal |  |  | owner=default |
| 40362 | 2026-09-05T05:54:55.846Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=3a8ef9bf9fbf250639966eacb5fedb15ee3165eed484540e7280d2129e30e822 |
| 40363 | 2026-09-05T05:54:56.415Z | observation_span_recorded |  |  |  |
| 40364 | 2026-09-05T05:54:56.614Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 40365 | 2026-09-05T06:27:33.939Z | observation_span_recorded |  |  |  |
| 40366 | 2026-09-05T06:27:34.163Z | failure_observed | ACCEPTING | ACCEPTING | reason=REPORT-PARTIAL-01 review rejection: schema_version currently accepts 1.0 via equality instead of exact integer 1; timestamp parsing lacks bounded canonical ASCII shape/offset validation before datetime parsing; and the current tests/implementation allow an applied_patch_delta_v1 observation with zero affected files to be marked complete even though the canonical producer contract requires at least one affected file. Focused 14-test pass is therefore insufficient for final acceptance.; failure_class=SOL_REJECTED |
| 40367 | 2026-09-05T06:27:34.377Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 40368 | 2026-09-05T06:27:34.675Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 3a8ef9bf9fbf250639966eacb5fedb15ee3165eed484540e7280d2129e30e822 | False | 17421 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `78`
- Chain head: `736a38f27e21bad55f4e9565dd11f6d227579187eb511c818545be70a128a251`
