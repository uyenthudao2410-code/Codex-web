# Orchestration Wave 2

- Run: `f455bda4374c4bf889fc479c8cb9c94c`
- Wave: `9b49b027d76a4a9cb7d218676778b100`
- Objective: Natural #20 candidate diagnostic only: inspect the exact immutable-ledger failure_observed to wave_replanned pairs behind the remaining generic CHECK_FAILED and BUILD_VERIFICATION_FAILED causal unknowns. Reuse the same diagnostic RUN, make no source changes, and determine whether any additional narrow high-confidence semantic correction patterns are actually evidenced.
- Objective revision: `2`
- Objective SHA-256: `6160d51a9b8b0a0f54ee6ecc6259eeb42d67060445e33d923f2692cbb1bbf337`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `106a86d0fc02094d1f8459e3f2182db3f4f50042902f6d7f0f2dd641f0396fe8`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 47333 | 2026-09-10T08:31:46.359Z | wave_replanned |  | PREFLIGHT | reason=Wave 1 proved the aggregate baseline but the CLI exposes no per-occurrence detail. Wave 2 changes evidence strategy: locate the immutable ledger read API/storage and extract exact paired generic failure/replan records read-only, without changing reporter/source. |
| 47334 | 2026-09-10T08:31:46.564Z | observation_span_recorded |  |  |  |
| 47335 | 2026-09-10T08:31:52.280Z | observation_span_recorded |  |  |  |
| 47336 | 2026-09-10T08:31:52.479Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 47337 | 2026-09-10T08:32:53.462Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 47338 | 2026-09-10T08:32:53.649Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 47339 | 2026-09-10T08:32:53.799Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 47340 | 2026-09-10T08:32:53.941Z | state_transition | READY | ROUTED | reason=route_selected |
| 47341 | 2026-09-10T08:32:54.209Z | observation_span_recorded |  |  |  |
| 47342 | 2026-09-10T08:32:55.259Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=81a5a17ac9db4c3cb12fc6866dc915ef |
| 47343 | 2026-09-10T08:32:55.811Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 47344 | 2026-09-10T08:32:56.706Z | observation_span_recorded |  |  |  |
| 47345 | 2026-09-10T08:32:57.000Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=81a5a17ac9db4c3cb12fc6866dc915ef |
| 47346 | 2026-09-10T08:32:57.130Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 47347 | 2026-09-10T08:32:57.993Z | proof_cache_miss |  |  | reason=cold; stage_id=check:85bea6415c1387d0; input_fingerprint=703ee6e83cf2393aa75cb4c1b0005751102d68709ad61782dbeef01e3e54a50a |
| 47348 | 2026-09-10T08:32:58.332Z | managed_process_admitted |  |  | owner=default |
| 47349 | 2026-09-10T08:32:58.917Z | managed_process_started |  |  | owner=default |
| 47350 | 2026-09-10T08:32:59.360Z | managed_process_terminal |  |  | owner=default |
| 47351 | 2026-09-10T08:32:59.717Z | proof_recorded |  |  | stage_id=check:85bea6415c1387d0; status=passed; cache_hit=False; input_fingerprint=703ee6e83cf2393aa75cb4c1b0005751102d68709ad61782dbeef01e3e54a50a |
| 47352 | 2026-09-10T08:32:59.877Z | proof_cache_miss |  |  | reason=cold; stage_id=check:eef3ad2ae75f81dc; input_fingerprint=85fe2ef08b8efbfff60d69a5b32f8da58dafafcaacbcb001a4cd58156cce405f |
| 47353 | 2026-09-10T08:33:00.182Z | managed_process_admitted |  |  | owner=default |
| 47354 | 2026-09-10T08:33:00.438Z | managed_process_started |  |  | owner=default |
| 47355 | 2026-09-10T08:33:00.906Z | managed_process_terminal |  |  | owner=default |
| 47356 | 2026-09-10T08:33:01.224Z | proof_recorded |  |  | stage_id=check:eef3ad2ae75f81dc; status=failed; cache_hit=False; input_fingerprint=85fe2ef08b8efbfff60d69a5b32f8da58dafafcaacbcb001a4cd58156cce405f |
| 47357 | 2026-09-10T08:33:01.382Z | observation_span_recorded |  |  |  |
| 47358 | 2026-09-10T08:33:01.547Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 47359 | 2026-09-10T08:33:01.731Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 47360 | 2026-09-10T08:33:01.899Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:85bea6415c1387d0 | passed | 703ee6e83cf2393aa75cb4c1b0005751102d68709ad61782dbeef01e3e54a50a | False | 1365 | 0 |
| check:eef3ad2ae75f81dc | failed | 85fe2ef08b8efbfff60d69a5b32f8da58dafafcaacbcb001a4cd58156cce405f | False | 1082 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `126`
- Chain head: `95dbefd4b89c56d59d1248e254ced9095acaca4fdbc0f70baaf619481bec7b52`
