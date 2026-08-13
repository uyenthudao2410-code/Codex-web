# Orchestration Wave 1

- Run: `92834371fba3419a8c0e065609835251`
- Wave: `3a7804be77e348deb9bc68580b3b33b9`
- Objective: Apply the supplied one-file test-harness patch exactly, then verify it. The patch removes process-global WEBCODEX_MCP_MODEL_SURFACE dependence from ordinary MCP test runtime construction while preserving explicit env-selection tests. Do not modify production code or any other file.
- Mode: `mcp_only`
- Base HEAD: `db7725e3601afc2692627a0b4eef674d599bd17e`
- Worktree fingerprint: `88b765e4cf53d9a3853a7c1868ea0a694e44eda49547a0e83922dea6f8fffae3`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 438 | 2026-08-13T17:43:33.592Z | run_started |  | PREFLIGHT |  |
| 439 | 2026-08-13T17:43:33.751Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=auto; resolved=mcp_only |
| 440 | 2026-08-13T17:43:33.845Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 441 | 2026-08-13T17:43:33.958Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 442 | 2026-08-13T17:43:34.051Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=auto; resolved=deterministic |
| 443 | 2026-08-13T17:43:34.162Z | state_transition | READY | ROUTED | reason=route_selected |
| 444 | 2026-08-13T17:43:34.479Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7db8dd91999b4538986ae3170840aaf1 |
| 445 | 2026-08-13T17:43:34.577Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 446 | 2026-08-13T17:43:34.929Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7db8dd91999b4538986ae3170840aaf1 |
| 447 | 2026-08-13T17:43:35.019Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 448 | 2026-08-13T17:43:37.111Z | proof_recorded |  |  | stage_id=check:edafbe150671a938; status=failed; cache_hit=False; input_fingerprint=d2714ce5a3b0d6e2f287212491cf021a163401e08b99af4bfd7f8700463a78a4 |
| 449 | 2026-08-13T17:43:37.220Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 450 | 2026-08-13T17:43:37.300Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:edafbe150671a938 | failed | d2714ce5a3b0d6e2f287212491cf021a163401e08b99af4bfd7f8700463a78a4 | False | 1707 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `fdfae5a031a1fcbc4e7a0080a0a1f03e653cef1359b0c6d1260d078d33641130`
