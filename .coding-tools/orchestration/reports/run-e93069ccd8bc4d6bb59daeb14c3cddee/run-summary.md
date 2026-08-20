# Orchestration Run Summary

- Run: `e93069ccd8bc4d6bb59daeb14c3cddee`
- Task: `805ee6d5effd4514930329f79ea926e3`
- Objective: S2/W0-W2 read-only audit after W3 acceptance. Localize the exact current implementation for W1 sparse model-facing projection and W2 artifact import/export/streaming in E:\DEV\Codex-web. Determine, from current source and focused tests, which upstream invariants are already present and which concrete gaps remain. W1 invariants: successful default tool results may use sparse/model-facing projections without changing non-default/failure semantics, proof/source identity, hashes/line counts, timeout/outcome_unknown, continuation or retry safety. W2 invariants: conversation attachment import, authenticated project export/resource, bounded streaming, cancellation/disconnect, atomic finalization, cleanup of partial transfers, content hash/provenance, and no duplicate artifact authority/public tool. Preserve current P4/P5 and smart-v3 8-tool contract. This is read-only audit: do not mutate source, docs, .coding-tools, Git state, runtime, or deployment. Return exact paths/symbols/tests and smallest evidence-backed delta candidates, distinguishing skip/adapt/port/defer.
- Status: **active**
- Started: `2026-08-20T11:22:47.834Z`
- Finished: `None`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `6659d288b4a749c391a3593b47d6c299` | `mcp_only` | `66c2d17b68969c3a413b867cc7281f80fbaf4b45` | replanned |
| 2 | `84706097ef7f4c81b87bb8b6edb35c89` | `mcp_only` | `66c2d17b68969c3a413b867cc7281f80fbaf4b45` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 23901 | `deterministic` | `deterministic` | explicit_request |
| 23923 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 23917 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `63`
- Chain head: `4bff2b05eb94b3c4e379ac5c293c742e9cd2b261bb76e4d2e81ae85ffb67466e`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
