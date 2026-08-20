# Orchestration Wave 2

- Run: `e93069ccd8bc4d6bb59daeb14c3cddee`
- Wave: `84706097ef7f4c81b87bb8b6edb35c89`
- Objective: S2/W0-W2 read-only audit after W3 acceptance. Localize the exact current implementation for W1 sparse model-facing projection and W2 artifact import/export/streaming in E:\DEV\Codex-web. Determine, from current source and focused tests, which upstream invariants are already present and which concrete gaps remain. W1 invariants: successful default tool results may use sparse/model-facing projections without changing non-default/failure semantics, proof/source identity, hashes/line counts, timeout/outcome_unknown, continuation or retry safety. W2 invariants: conversation attachment import, authenticated project export/resource, bounded streaming, cancellation/disconnect, atomic finalization, cleanup of partial transfers, content hash/provenance, and no duplicate artifact authority/public tool. Preserve current P4/P5 and smart-v3 8-tool contract. This is read-only audit: do not mutate source, docs, .coding-tools, Git state, runtime, or deployment. Return exact paths/symbols/tests and smallest evidence-backed delta candidates, distinguishing skip/adapt/port/defer.
- Mode: `mcp_only`
- Base HEAD: `66c2d17b68969c3a413b867cc7281f80fbaf4b45`
- Worktree fingerprint: `49df1bd45be44847a81ecf6f72ac256ef772a2548b2ee066fa371120889e626c`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 23920 | 2026-08-20T11:28:08.740Z | wave_replanned |  | PREFLIGHT | reason=The prior W1 wave made zero source writes and failed only because the broad existing work_on_project filter is not a valid current oracle on this host: 15 tests fail because test subprocesses cannot locate git, and one stale fixture uses a relative path while current contract requires absolute paths. Root-package rustfmt passed. Changed strategy: use a Sol xhigh deep-code candidate for the high-integration projection patch, keep MCP as sole writer/proof plane, and validate with new pure sparsification tests plus existing projection-only tests that do not depend on external git. Do not weaken or modify the unrelated baseline failures. |
| 23921 | 2026-08-20T11:28:08.971Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 23922 | 2026-08-20T11:28:09.211Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 23923 | 2026-08-20T11:28:09.370Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 23924 | 2026-08-20T11:28:09.522Z | state_transition | READY | ROUTED | reason=route_selected |
| 23925 | 2026-08-20T11:28:09.972Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7e75a24d356942d98f69a3d5d9131790 |
| 23926 | 2026-08-20T11:28:10.220Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 23927 | 2026-08-20T11:28:10.722Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7e75a24d356942d98f69a3d5d9131790 |
| 23928 | 2026-08-20T11:28:10.930Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 23929 | 2026-08-20T11:28:11.294Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:796009f75ffcdfa8; input_fingerprint=5de34d064bc64b7372b445aa934193db9de5a30f130a5cc7601d1c8e6e8901cd |
| 23930 | 2026-08-20T11:28:11.644Z | managed_process_admitted |  |  | owner=default |
| 23931 | 2026-08-20T11:28:11.910Z | managed_process_started |  |  | owner=default |
| 23932 | 2026-08-20T11:28:15.690Z | managed_process_terminal |  |  | owner=default |
| 23933 | 2026-08-20T11:28:16.170Z | proof_recorded |  |  | stage_id=check:796009f75ffcdfa8; status=passed; cache_hit=False; input_fingerprint=5de34d064bc64b7372b445aa934193db9de5a30f130a5cc7601d1c8e6e8901cd |
| 23934 | 2026-08-20T11:28:16.340Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:all; input_fingerprint=8392025387041075b4e96edbfdde3cb3c39bf6a67e70ddfb707393f664f8e790 |
| 23935 | 2026-08-20T11:28:16.701Z | managed_process_admitted |  |  | owner=default |
| 23936 | 2026-08-20T11:28:17.066Z | managed_process_started |  |  | owner=default |
| 23937 | 2026-08-20T11:28:19.125Z | managed_process_terminal |  |  | owner=default |
| 23938 | 2026-08-20T11:28:19.534Z | managed_process_admitted |  |  | owner=default |
| 23939 | 2026-08-20T11:28:19.825Z | managed_process_started |  |  | owner=default |
| 23940 | 2026-08-20T11:28:20.851Z | managed_process_terminal |  |  | owner=default |
| 23941 | 2026-08-20T11:28:29.165Z | proof_recorded |  |  | stage_id=verify:all; status=passed; cache_hit=False; input_fingerprint=8392025387041075b4e96edbfdde3cb3c39bf6a67e70ddfb707393f664f8e790 |
| 23942 | 2026-08-20T11:28:29.455Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:796009f75ffcdfa8 | passed | 5de34d064bc64b7372b445aa934193db9de5a30f130a5cc7601d1c8e6e8901cd | False | 4467 | 0 |
| verify:all | passed | 8392025387041075b4e96edbfdde3cb3c39bf6a67e70ddfb707393f664f8e790 | False | 12344 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `63`
- Chain head: `4bff2b05eb94b3c4e379ac5c293c742e9cd2b261bb76e4d2e81ae85ffb67466e`
