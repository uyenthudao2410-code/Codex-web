# Orchestration Run Summary

- Run: `e93069ccd8bc4d6bb59daeb14c3cddee`
- Task: `805ee6d5effd4514930329f79ea926e3`
- Objective: S2/W0-W2 read-only audit after W3 acceptance. Localize the exact current implementation for W1 sparse model-facing projection and W2 artifact import/export/streaming in E:\DEV\Codex-web. Determine, from current source and focused tests, which upstream invariants are already present and which concrete gaps remain. W1 invariants: successful default tool results may use sparse/model-facing projections without changing non-default/failure semantics, proof/source identity, hashes/line counts, timeout/outcome_unknown, continuation or retry safety. W2 invariants: conversation attachment import, authenticated project export/resource, bounded streaming, cancellation/disconnect, atomic finalization, cleanup of partial transfers, content hash/provenance, and no duplicate artifact authority/public tool. Preserve current P4/P5 and smart-v3 8-tool contract. This is read-only audit: do not mutate source, docs, .coding-tools, Git state, runtime, or deployment. Return exact paths/symbols/tests and smallest evidence-backed delta candidates, distinguishing skip/adapt/port/defer.
- Status: **accepted**
- Started: `2026-08-20T11:22:47.834Z`
- Finished: `2026-08-20T12:50:15.082Z`

## Outcome metrics

- Waves: **8**
- Route decisions: **7**
- Failures observed: **7**
- REPLAN transitions: **7**
- Proof stages: **10**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `6659d288b4a749c391a3593b47d6c299` | `mcp_only` | `66c2d17b68969c3a413b867cc7281f80fbaf4b45` | replanned |
| 2 | `84706097ef7f4c81b87bb8b6edb35c89` | `mcp_only` | `66c2d17b68969c3a413b867cc7281f80fbaf4b45` | replanned |
| 3 | `d0384c40d65846ecadaa5cde5863aca7` | `mcp_only` | `936c3dbe10f40f097e63bf0e0aa6e6498ab7957f` | replanned |
| 4 | `e95b302239814d46bc8b8b7c82aa1b5c` | `mcp_only` | `936c3dbe10f40f097e63bf0e0aa6e6498ab7957f` | replanned |
| 5 | `818e5cf22af6405497c7629503fc9870` | `mcp_only` | `4db5ac764be4328edf76245bd1214fb953c2460e` | replanned |
| 6 | `86344d01240f4f90a8325092d2711065` | `mcp_only` | `4db5ac764be4328edf76245bd1214fb953c2460e` | replanned |
| 7 | `b79ed8f02d6f405d8baae3b16d8b09c0` | `mcp_only` | `28a5f62f3f01d3a78d851beffd9a2c6a72f8302a` | replanned |
| 8 | `23672f6af4394df49b6a5204d8d76269` | `mcp_only` | `28a5f62f3f01d3a78d851beffd9a2c6a72f8302a` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| b3432eec3c9b4ee69793734d8a4a630f | 23672f6af4394df49b6a5204d8d76269 | accepted | 28a5f62f3f01d3a78d851beffd9a2c6a72f8302a | abf0a8f7f280c138070d0ab3d53e6907f6ad8fd96a3fe399d8a64356dab1de6d | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 23901 | `deterministic` | `deterministic` | explicit_request |
| 23923 | `deterministic` | `deterministic` | explicit_request |
| 23952 | `deterministic` | `deterministic` | explicit_request |
| 24029 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 24050 | `deterministic` | `deterministic` | explicit_request |
| 24074 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 24092 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 23917 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 23946 | `SOL_REJECTED` | `ACCEPTING` | Controller rejection: acceptance oracle was false-green. Current source tree has no W1 required symbols include_project_instructions/include_workflow_guidance or the three required sparsifiers, and Git diff contains no W1 source changes. Focused cargo test filters passed without proving implementation presence. Replan must add explicit source-presence assertions/non-zero matching regression tests and implement W1 deterministically before acceptance. |
| 23963 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 24023 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 24044 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 24061 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 24086 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `235`
- Chain head: `70c3bcfdbbd73c573e8d80a46a4d343ba287a3d1bb6522d41ae64011a48c311c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
