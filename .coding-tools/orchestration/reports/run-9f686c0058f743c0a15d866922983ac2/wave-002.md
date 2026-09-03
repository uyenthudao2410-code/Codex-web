# Orchestration Wave 2

- Run: `9f686c0058f743c0a15d866922983ac2`
- Wave: `8b98e4a92cfe47f6b798982d863cf1cd`
- Objective: W8 only: implement the budget/reservation control defined by docs/research/260901_CODING_WEB_TOKEN_USAGE_COST_CONTEXT_OBSERVABILITY_AND_ACCEPTED_RESULT_EFFICIENCY_MASTER_PLAN.md on top of accepted W1-W7. Preserve unknown_not_zero, never convert bytes to tokens, never treat estimates as observed spend, preserve exact 8-tool smart-v3 public MCP contract, fail closed on missing/stale reservation authority, and keep controller/provider/tool-card accounting planes distinct. Exclude W9 history analytics and W10 representative E2E closure. Do not commit, push, restart, package, release, or deploy. First localize the exact W8 contract, existing budget/credit/routing admission surfaces, reservation lifecycle authority, smallest causal change set, and focused deterministic proof plan while preserving unrelated dirty work.
- Objective revision: `1`
- Objective SHA-256: `505f6c1333dad0dafe302b0b2d2828cb326fc58c48009987c5dcbec79349760d`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `bfd17766ca0b2c128875d7811865e09b205f58c02865be4baf5303e0734316af`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 35005 | 2026-09-01T23:41:26.022Z | wave_replanned |  | PREFLIGHT | reason=Replacement W8 after canonical reconciliation. Prior wave 26cdb21ffdbf4e2aa62fd68c3631c2f7 was rejected as a no-op; canonical events after seq 34928 are empty, so no ambiguous write/lease exists. Implement durable UsageReservation -> actual UsageEvent reconciliation with fresh authority only. Require a fresh wave, fresh P4 solution shadow before first mutation, a real write lease, non-empty source receipts, and fresh current-code proofs. Old no-op proofs are invalid and must not be reused. Preserve unknown_not_zero; bytes are never tokens; estimates are never observed spend; exact actual usage is valid only when measured telemetry is exact; terminal missing exact usage closes indeterminate rather than zero; public smart-v3 tool contract remains exactly 8 tools. |
| 35006 | 2026-09-01T23:41:26.308Z | observation_span_recorded |  |  |  |
| 35007 | 2026-09-01T23:41:44.508Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 35008 | 2026-09-01T23:41:44.720Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 35009 | 2026-09-01T23:41:44.928Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 35010 | 2026-09-01T23:41:45.135Z | state_transition | READY | ROUTED | reason=route_selected |
| 35011 | 2026-09-01T23:41:45.433Z | observation_span_recorded |  |  |  |
| 35012 | 2026-09-01T23:41:46.458Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=8fb8e8ad535144ac9dd1cb611da90611 |
| 35013 | 2026-09-01T23:41:46.658Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 35014 | 2026-09-01T23:41:47.472Z | observation_span_recorded |  |  |  |
| 35015 | 2026-09-01T23:41:47.782Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=8fb8e8ad535144ac9dd1cb611da90611 |
| 35016 | 2026-09-01T23:41:47.965Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 35017 | 2026-09-01T23:41:48.826Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=72d5104599facb4b06d235a89cde3f06e02cfbe107b3c4bbb04cd4684efae77e |
| 35018 | 2026-09-01T23:41:49.226Z | managed_process_admitted |  |  | owner=default |
| 35019 | 2026-09-01T23:41:49.529Z | managed_process_started |  |  | owner=default |
| 35020 | 2026-09-01T23:42:03.642Z | managed_process_terminal |  |  | owner=default |
| 35021 | 2026-09-01T23:42:04.081Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=72d5104599facb4b06d235a89cde3f06e02cfbe107b3c4bbb04cd4684efae77e |
| 35022 | 2026-09-01T23:42:04.458Z | observation_span_recorded |  |  |  |
| 35023 | 2026-09-01T23:42:04.708Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 35024 | 2026-09-01T23:42:04.935Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 35025 | 2026-09-01T23:42:05.205Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 72d5104599facb4b06d235a89cde3f06e02cfbe107b3c4bbb04cd4684efae77e | False | 14858 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `213`
- Chain head: `c1a389deacb2a94e0d3a41945bc45e06a8683ae9fd08dc14ea77507c7bac983a`
