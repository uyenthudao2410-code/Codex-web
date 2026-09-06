# Orchestration Wave 4

- Run: `4135fb1a2afd49c787a8fa7f0dd87cb0`
- Wave: `18004d86286a443781430706870ed561`
- Objective: REPORT-PARTIAL-01 corrective replan: inspect only operator_report.py and test_operator_report_isolation.py before applying the reviewed report-projection correction. Preserve all unrelated WIP and the rejected endpoint-test wave as unaccepted.
- Objective revision: `3`
- Objective SHA-256: `454b5cf37691ac814ee40f13b5d344e60db7ad78807ee86de1bcdddc2eb8b20e`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `8697ace8204e7e3da55d250d4a52d9b2b930116c`
- Worktree fingerprint: `92077f52bf6982ffc0e52427525dc3c6587c9c9e20181695b1a4eed6f8087d76`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 40385 | 2026-09-05T07:31:35.122Z | wave_replanned |  | PREFLIGHT | reason=REPORT-PARTIAL-01 changed-strategy correction after rejected review: require exact integer schema_version 1, bounded canonical ASCII timestamp validation, and at least one affected-file identity for a complete applied-patch observation; preserve the existing report projection design and omit overlapping existing-file adoption. |
| 40386 | 2026-09-05T07:31:35.310Z | observation_span_recorded |  |  |  |
| 40387 | 2026-09-05T07:31:53.522Z | observation_span_recorded |  |  |  |
| 40388 | 2026-09-05T07:31:53.713Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 40389 | 2026-09-05T07:32:55.036Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 40390 | 2026-09-05T07:32:55.187Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 40391 | 2026-09-05T07:32:55.386Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 40392 | 2026-09-05T07:32:55.603Z | state_transition | READY | ROUTED | reason=route_selected |
| 40393 | 2026-09-05T07:32:55.870Z | observation_span_recorded |  |  |  |
| 40394 | 2026-09-05T07:32:56.456Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1033a98e14d34775a48df8a18f8da9f7 |
| 40395 | 2026-09-05T07:32:56.674Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 40396 | 2026-09-05T07:32:57.194Z | patch_surface_observed |  |  |  |
| 40397 | 2026-09-05T07:32:57.440Z | patch_surface_observed |  |  |  |
| 40398 | 2026-09-05T07:32:57.655Z | observation_span_recorded |  |  |  |
| 40399 | 2026-09-05T07:32:57.953Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1033a98e14d34775a48df8a18f8da9f7 |
| 40400 | 2026-09-05T07:32:58.121Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 40401 | 2026-09-05T07:32:58.622Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=ca9236f5cce89307e445a55402bb39e15965c4635be862176cd3398e0d7d0922 |
| 40402 | 2026-09-05T07:32:59.003Z | managed_process_admitted |  |  | owner=default |
| 40403 | 2026-09-05T07:32:59.313Z | managed_process_started |  |  | owner=default |
| 40404 | 2026-09-05T07:33:14.288Z | managed_process_terminal |  |  | owner=default |
| 40405 | 2026-09-05T07:33:22.052Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=ca9236f5cce89307e445a55402bb39e15965c4635be862176cd3398e0d7d0922 |
| 40406 | 2026-09-05T07:33:22.803Z | observation_span_recorded |  |  |  |
| 40407 | 2026-09-05T07:33:23.139Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 40408 | 2026-09-05T07:47:55.304Z | quality_outcome_recorded |  |  |  |
| 40409 | 2026-09-05T07:47:55.502Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 40410 | 2026-09-05T07:47:55.905Z | observation_span_recorded |  |  |  |
| 40411 | 2026-09-05T07:47:56.205Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | ca9236f5cce89307e445a55402bb39e15965c4635be862176cd3398e0d7d0922 | False | 22844 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 914b8c816f1e42ffa793a8c7c976e90f | accepted | 8697ace8204e7e3da55d250d4a52d9b2b930116c | 24002d4b198cb88ca916b8898fb80464cf2ba26c8764b7447c3a49a4a12476d7 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `78`
- Chain head: `736a38f27e21bad55f4e9565dd11f6d227579187eb511c818545be70a128a251`
