# Orchestration Wave 1

- Run: `3ed74c091e6447929542501bff04667c`
- Wave: `cdfe40844d7f4942995cf3125b40caf3`
- Objective: Re-prove P3A after fixing only the missing unittest.mock.patch fixture import.
- Mode: `mcp_only`
- Base HEAD: `5decaa48300b10a6df39676c677745bc881cd7d9`
- Worktree fingerprint: `3b699db33e4cbede40158b4735c354cb0893a9e1e63adc7483f983ca3182ef9c`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 3299 | 2026-08-14T18:11:23.829Z | run_started |  | PREFLIGHT |  |
| 3300 | 2026-08-14T18:11:23.970Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 3301 | 2026-08-14T18:11:24.077Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 3302 | 2026-08-14T18:11:24.195Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 3303 | 2026-08-14T18:11:24.327Z | state_transition | READY | ROUTED | reason=route_selected |
| 3304 | 2026-08-14T18:11:24.809Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4596c1a80fcc420aabf755115b5c04bf |
| 3305 | 2026-08-14T18:11:24.935Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 3306 | 2026-08-14T18:11:25.500Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4596c1a80fcc420aabf755115b5c04bf |
| 3307 | 2026-08-14T18:11:25.662Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 3308 | 2026-08-14T18:11:26.052Z | proof_cache_miss |  |  | reason=cold; stage_id=check:56029c100af28fc0; input_fingerprint=1c7143d37a22a1c306003a7af68da3a9eac52d3b6de15087f682dfbb43e2b2ef |
| 3309 | 2026-08-14T18:11:27.867Z | proof_recorded |  |  | stage_id=check:56029c100af28fc0; status=passed; cache_hit=False; input_fingerprint=1c7143d37a22a1c306003a7af68da3a9eac52d3b6de15087f682dfbb43e2b2ef |
| 3310 | 2026-08-14T18:11:36.230Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 3311 | 2026-08-14T18:11:47.225Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:56029c100af28fc0 | passed | 1c7143d37a22a1c306003a7af68da3a9eac52d3b6de15087f682dfbb43e2b2ef | False | 1544 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 1728ef9c5b9443d3a7c2381f70271d09 | accepted | 5decaa48300b10a6df39676c677745bc881cd7d9 | 3ec547991478ba4e2e517ec04179fe5ce3dbdc7725e97f3677f6562274ce2416 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `2a02224a9db4611e4eabee02750fbe2a0c06c6c58ed8c006d83826af34a764a0`
