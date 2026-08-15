# Orchestration Wave 1

- Run: `f3329039dff745edbd4dcaba416d5507`
- Wave: `b466227c76f843c385d8c01e3a704978`
- Objective: Finalize proof for the accepted-result measurement and paired-policy evaluation plane already written in the prior wave. Do not mutate source in this wave. Verify normalized accepted-result evaluation, paired representative policy comparison, evaluation schema, CLI availability, and whitespace integrity.
- Mode: `mcp_only`
- Base HEAD: `dff81e251836666fc825c40bf86e4167afd29c39`
- Worktree fingerprint: `3b4f42294bffc90011570aa8d1b72b2422e73c054c91a1a8d8d9ac83c36c38ca`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4140 | 2026-08-15T04:20:06.828Z | run_started |  | PREFLIGHT |  |
| 4141 | 2026-08-15T04:20:06.997Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4142 | 2026-08-15T04:20:07.197Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4143 | 2026-08-15T04:20:07.410Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 4144 | 2026-08-15T04:20:07.610Z | state_transition | READY | ROUTED | reason=route_selected |
| 4145 | 2026-08-15T04:20:08.177Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f0a153e3f58e43418cc65523b471afe5 |
| 4146 | 2026-08-15T04:20:08.406Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4147 | 2026-08-15T04:20:08.944Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f0a153e3f58e43418cc65523b471afe5 |
| 4148 | 2026-08-15T04:20:09.151Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4149 | 2026-08-15T04:20:09.556Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=b0db48c4ab2876db9124bb63e567d7bc816b17773fe6a77e63cb1bc04641a836 |
| 4150 | 2026-08-15T04:20:11.038Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=b0db48c4ab2876db9124bb63e567d7bc816b17773fe6a77e63cb1bc04641a836 |
| 4151 | 2026-08-15T04:20:11.269Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 4152 | 2026-08-15T04:20:11.470Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | b0db48c4ab2876db9124bb63e567d7bc816b17773fe6a77e63cb1bc04641a836 | False | 1094 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `bd57a78c50dbc7d98e4e3ecfcbe996ac6f04173a681c46c710fd54bac2b1af01`
