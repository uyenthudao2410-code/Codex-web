# Orchestration Wave 1

- Run: `41970794950d4183aa09b0e0b063fec1`
- Wave: `6efc6cda64044c829525eadc446c70e8`
- Objective: Post-activation live L3 token-observability canary only. Run exactly the read-only runtime oracle npm run dev:status on E:\DEV\Codex-web under the current attested ChatWeb transport. Do not mutate source, do not trust or accept caller-supplied evaluation turn_id/trace_id, do not commit/push/release/deploy. The purpose is to let the runtime derive authoritative content-free host correlation from the current attested ChatWeb transport trace and later verify exact controller usage if a valid receipt arrives.
- Objective revision: `1`
- Objective SHA-256: `7c4ef9082adbbd9efd6959b48caa93f0e6d34fd480deb8fe421f754b0288eb33`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `6b5fb2badfbcfa32b95881356c90eb51b89d687739b0b7df90dd27ec25209209`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 38059 | 2026-09-03T16:47:37.368Z | run_started |  | PREFLIGHT |  |
| 38062 | 2026-09-03T16:47:38.694Z | observation_span_recorded |  |  |  |
| 38063 | 2026-09-03T16:47:39.624Z | observation_span_recorded |  |  |  |
| 38064 | 2026-09-03T16:47:39.853Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 38066 | 2026-09-03T16:47:40.262Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 38068 | 2026-09-03T16:47:40.670Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 38069 | 2026-09-03T16:47:40.844Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 38070 | 2026-09-03T16:47:41.069Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 38071 | 2026-09-03T16:47:41.265Z | state_transition | READY | ROUTED | reason=route_selected |
| 38073 | 2026-09-03T16:47:41.898Z | observation_span_recorded |  |  |  |
| 38075 | 2026-09-03T16:47:43.043Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=67e2cf7560ac4be1addf65768bb19305 |
| 38076 | 2026-09-03T16:47:43.261Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 38084 | 2026-09-03T16:47:45.378Z | observation_span_recorded |  |  |  |
| 38085 | 2026-09-03T16:47:45.706Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=67e2cf7560ac4be1addf65768bb19305 |
| 38086 | 2026-09-03T16:47:45.892Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 38089 | 2026-09-03T16:47:46.814Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:385f51573288f6e6; input_fingerprint=a53e285c58da589f6f43929d1b28cce208edef43a5ab9618e79ae8e60f514de3 |
| 38090 | 2026-09-03T16:47:47.569Z | managed_process_admitted |  |  | owner=default |
| 38092 | 2026-09-03T16:47:48.233Z | managed_process_started |  |  | owner=default |
| 38096 | 2026-09-03T16:47:49.746Z | managed_process_terminal |  |  | owner=default |
| 38097 | 2026-09-03T16:47:50.184Z | proof_recorded |  |  | stage_id=check:385f51573288f6e6; status=passed; cache_hit=False; input_fingerprint=a53e285c58da589f6f43929d1b28cce208edef43a5ab9618e79ae8e60f514de3 |
| 38099 | 2026-09-03T16:47:50.672Z | observation_span_recorded |  |  |  |
| 38100 | 2026-09-03T16:47:50.884Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 38116 | 2026-09-03T16:48:19.363Z | quality_outcome_recorded |  |  |  |
| 38117 | 2026-09-03T16:48:19.658Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 38118 | 2026-09-03T16:48:19.955Z | observation_span_recorded |  |  |  |
| 38119 | 2026-09-03T16:48:20.197Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:385f51573288f6e6 | passed | a53e285c58da589f6f43929d1b28cce208edef43a5ab9618e79ae8e60f514de3 | False | 2880 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 2ee99c6523b746feb64bdcaa80993aeb | accepted | 80aceb583202ad381c25687969fb48adbf74622c | a7d1826acc455f285726cb2253e0ab573114ccb6daac4df75e66f94e891e54c0 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `0b76c2e3aabec1a5213cbc2493b2e04db9d2f2f3e6dc6fe5b4575afb82715f3b`
