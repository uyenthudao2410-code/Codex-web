# Orchestration Wave 5

- Run: `e93069ccd8bc4d6bb59daeb14c3cddee`
- Wave: `818e5cf22af6405497c7629503fc9870`
- Objective: S2/W0-W2 read-only audit after W3 acceptance. Localize the exact current implementation for W1 sparse model-facing projection and W2 artifact import/export/streaming in E:\DEV\Codex-web. Determine, from current source and focused tests, which upstream invariants are already present and which concrete gaps remain. W1 invariants: successful default tool results may use sparse/model-facing projections without changing non-default/failure semantics, proof/source identity, hashes/line counts, timeout/outcome_unknown, continuation or retry safety. W2 invariants: conversation attachment import, authenticated project export/resource, bounded streaming, cancellation/disconnect, atomic finalization, cleanup of partial transfers, content hash/provenance, and no duplicate artifact authority/public tool. Preserve current P4/P5 and smart-v3 8-tool contract. This is read-only audit: do not mutate source, docs, .coding-tools, Git state, runtime, or deployment. Return exact paths/symbols/tests and smallest evidence-backed delta candidates, distinguishing skip/adapt/port/defer.
- Mode: `mcp_only`
- Base HEAD: `4db5ac764be4328edf76245bd1214fb953c2460e`
- Worktree fingerprint: `690d461663c1f94b329cb112d77851c480f231620e6bd6e8374562095d292268`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 24026 | 2026-08-20T12:00:51.769Z | wave_replanned |  | PREFLIGHT | reason=Two prior submissions were rejected during patch preflight only because the test insertion context was ambiguous; no source mutation occurred. This retry anchors directly on the unique next test function and keeps the same controller-approved W1 design and hardened acceptance oracle. |
| 24027 | 2026-08-20T12:00:51.946Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 24028 | 2026-08-20T12:00:52.090Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 24029 | 2026-08-20T12:00:52.299Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 24030 | 2026-08-20T12:00:52.507Z | state_transition | READY | ROUTED | reason=route_selected |
| 24031 | 2026-08-20T12:00:52.990Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=949f1cb52794496ba1f6f3805a5af96a |
| 24032 | 2026-08-20T12:00:53.168Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 24033 | 2026-08-20T12:00:53.619Z | patch_surface_observed |  |  |  |
| 24034 | 2026-08-20T12:00:53.985Z | patch_surface_observed |  |  |  |
| 24035 | 2026-08-20T12:00:54.192Z | patch_surface_observed |  |  |  |
| 24036 | 2026-08-20T12:00:54.446Z | patch_surface_observed |  |  |  |
| 24037 | 2026-08-20T12:00:54.827Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=949f1cb52794496ba1f6f3805a5af96a |
| 24038 | 2026-08-20T12:00:55.011Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 24039 | 2026-08-20T12:00:55.414Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:all; input_fingerprint=c650dadfc6e105ee52a9e7f0b3f464b31c6a98b4468bc3431f805136f7156ed3 |
| 24040 | 2026-08-20T12:00:55.797Z | managed_process_admitted |  |  | owner=default |
| 24041 | 2026-08-20T12:00:56.058Z | managed_process_started |  |  | owner=default |
| 24042 | 2026-08-20T12:00:57.477Z | managed_process_terminal |  |  | owner=default |
| 24043 | 2026-08-20T12:00:57.826Z | proof_recorded |  |  | stage_id=verify:all; status=failed; cache_hit=False; input_fingerprint=c650dadfc6e105ee52a9e7f0b3f464b31c6a98b4468bc3431f805136f7156ed3 |
| 24044 | 2026-08-20T12:00:58.044Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 24045 | 2026-08-20T12:00:58.241Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 24046 | 2026-08-20T12:00:58.445Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:all | failed | c650dadfc6e105ee52a9e7f0b3f464b31c6a98b4468bc3431f805136f7156ed3 | False | 2094 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `235`
- Chain head: `70c3bcfdbbd73c573e8d80a46a4d343ba287a3d1bb6522d41ae64011a48c311c`
