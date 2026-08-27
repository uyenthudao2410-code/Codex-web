# Orchestration Wave 1

- Run: `8b8e5b92bf814969bbd21f1577056275`
- Wave: `d0f34ba1ff594bfd9fce14f2c6dbb371`
- Objective: Create one durable read-only deterministic final-acceptance proof RUN/WAVE for the current implementation of full-clean activation at exact Git HEAD 898d57454f9a5113d8aa3f56d1650e4b3e0d6924. Do not modify source, do not clean/reset/revert, do not touch ledger.sqlite3 manually, do not push/tag/release/deploy, and do not restart runtime. Run or exactly reuse fingerprint-matching proof for `npm test` only, then leave this new wave at ACCEPTING if proof passes.
- Objective revision: `1`
- Objective SHA-256: `4e41b9c5350813bc0f8c47bc3705ef9caff96de7ce0b7506289720995fae01ed`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `898d57454f9a5113d8aa3f56d1650e4b3e0d6924`
- Worktree fingerprint: `f0f534fc13eb8768dd1f47c07466cf557157d03e175f0c3ef5383ceb67c4b197`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 30751 | 2026-08-26T13:13:17.320Z | run_started |  | PREFLIGHT |  |
| 30752 | 2026-08-26T13:13:17.615Z | observation_span_recorded |  |  |  |
| 30753 | 2026-08-26T13:13:18.442Z | observation_span_recorded |  |  |  |
| 30754 | 2026-08-26T13:13:18.597Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 30755 | 2026-08-26T13:13:18.912Z | managed_process_admitted |  |  | owner=default |
| 30756 | 2026-08-26T13:13:19.170Z | managed_process_started |  |  | owner=default |
| 30757 | 2026-08-26T13:14:01.912Z | managed_process_terminal |  |  | owner=default |
| 30758 | 2026-08-26T13:14:02.057Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 30759 | 2026-08-26T13:14:02.213Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 30760 | 2026-08-26T13:14:02.354Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 30761 | 2026-08-26T13:14:02.487Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 30762 | 2026-08-26T13:14:02.670Z | state_transition | READY | ROUTED | reason=route_selected |
| 30763 | 2026-08-26T13:14:02.855Z | observation_span_recorded |  |  |  |
| 30764 | 2026-08-26T13:14:03.631Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=6d4d30b9ed4c4c5b924c3a27167432b6 |
| 30765 | 2026-08-26T13:14:03.771Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 30766 | 2026-08-26T13:14:04.510Z | observation_span_recorded |  |  |  |
| 30767 | 2026-08-26T13:14:04.722Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=6d4d30b9ed4c4c5b924c3a27167432b6 |
| 30768 | 2026-08-26T13:14:04.846Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 30769 | 2026-08-26T13:14:05.525Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=803859d113b92876ba1f580c663183c0523661f089b8733bf13710f096047494 |
| 30770 | 2026-08-26T13:14:05.813Z | managed_process_admitted |  |  | owner=default |
| 30771 | 2026-08-26T13:14:06.097Z | managed_process_started |  |  | owner=default |
| 30772 | 2026-08-26T13:14:45.737Z | managed_process_terminal |  |  | owner=default |
| 30773 | 2026-08-26T13:14:46.079Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=803859d113b92876ba1f580c663183c0523661f089b8733bf13710f096047494 |
| 30774 | 2026-08-26T13:14:46.273Z | observation_span_recorded |  |  |  |
| 30775 | 2026-08-26T13:14:46.415Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 30776 | 2026-08-26T13:14:46.603Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 30777 | 2026-08-26T13:14:46.781Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 803859d113b92876ba1f580c663183c0523661f089b8733bf13710f096047494 | False | 40250 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `56`
- Chain head: `648d9eae3cd8283c36399c68d09e3e46aa66b3c965fc2791e03c1b3f452c8072`
