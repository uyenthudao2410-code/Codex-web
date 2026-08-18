# Orchestration Wave 1

- Run: `1792024eddad473ebad50e3bd3e5351d`
- Wave: `e5e4281ebdbd4229b83b1e41916e3b57`
- Objective: Verify the committed P1 ITT hardening at HEAD bc17700e before any P3 treatment. Do not modify source. Confirm the regression test for a nonaccepted SERVER_FIRST_DETERMINISTIC_V1 candidate that replanned remains in the intention-to-treat denominator and yields candidate_acceptance_rate=0, candidate_first_pass_rate=0, candidate_repair_rate=1. Then run the paired-policy CLI help/current no-pair comparison for LOCAL_FIRST_V1 vs SERVER_FIRST_DETERMINISTIC_V1 and confirm missing controller token/monetary cost remains unknown rather than zero. This is verification only, not representative enrollment.
- Mode: `mcp_only`
- Base HEAD: `bc17700e475ce74c96a9547117aade58823f0811`
- Worktree fingerprint: `e8c159440c324c40eb2c8f2f3d85416a377d64be6d5c466ea3d0bd1089609264`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 15892 | 2026-08-17T23:27:03.311Z | run_started |  | PREFLIGHT |  |
| 15893 | 2026-08-17T23:27:03.672Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 15894 | 2026-08-17T23:27:03.930Z | managed_process_admitted |  |  | owner=default |
| 15895 | 2026-08-17T23:27:04.136Z | managed_process_started |  |  | owner=default |
| 15896 | 2026-08-17T23:27:06.096Z | managed_process_terminal |  |  | owner=default |
| 15897 | 2026-08-17T23:27:06.191Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 15898 | 2026-08-17T23:27:06.318Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 15899 | 2026-08-17T23:27:06.429Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 15900 | 2026-08-17T23:27:06.540Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 15901 | 2026-08-17T23:27:06.657Z | state_transition | READY | ROUTED | reason=route_selected |
| 15902 | 2026-08-17T23:27:07.040Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=f3ca28cad89e4f25b65ddc67a439efdc |
| 15903 | 2026-08-17T23:27:07.147Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 15904 | 2026-08-17T23:27:07.530Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=f3ca28cad89e4f25b65ddc67a439efdc |
| 15905 | 2026-08-17T23:27:07.678Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 15906 | 2026-08-17T23:27:08.019Z | proof_cache_miss |  |  | reason=cold; stage_id=check:1a9b573680690d76; input_fingerprint=bd70239045f4989dd01ee385082f3ff93c00f4f3aacec9da062efc6dde58e714 |
| 15907 | 2026-08-17T23:27:08.239Z | managed_process_admitted |  |  | owner=default |
| 15908 | 2026-08-17T23:27:08.445Z | managed_process_started |  |  | owner=default |
| 15909 | 2026-08-17T23:27:14.926Z | managed_process_terminal |  |  | owner=default |
| 15910 | 2026-08-17T23:27:15.142Z | proof_recorded |  |  | stage_id=check:1a9b573680690d76; status=passed; cache_hit=False; input_fingerprint=bd70239045f4989dd01ee385082f3ff93c00f4f3aacec9da062efc6dde58e714 |
| 15911 | 2026-08-17T23:27:15.279Z | proof_cache_miss |  |  | reason=cold; stage_id=check:0650d77ec561a074; input_fingerprint=57c6017860a3d5e87c1d7244433880812c4a441e81e7f87c8ef0dff97d18f2c3 |
| 15912 | 2026-08-17T23:27:15.539Z | managed_process_admitted |  |  | owner=default |
| 15913 | 2026-08-17T23:27:15.762Z | managed_process_started |  |  | owner=default |
| 15914 | 2026-08-17T23:27:16.118Z | managed_process_terminal |  |  | owner=default |
| 15915 | 2026-08-17T23:27:16.372Z | proof_recorded |  |  | stage_id=check:0650d77ec561a074; status=passed; cache_hit=False; input_fingerprint=57c6017860a3d5e87c1d7244433880812c4a441e81e7f87c8ef0dff97d18f2c3 |
| 15916 | 2026-08-17T23:27:16.508Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=80bcfafc732469b0f9a6ca003bf96912e74454adc53c5940ca49acebf908a067 |
| 15917 | 2026-08-17T23:27:16.742Z | managed_process_admitted |  |  | owner=default |
| 15918 | 2026-08-17T23:27:16.946Z | managed_process_started |  |  | owner=default |
| 15919 | 2026-08-17T23:27:20.013Z | managed_process_terminal |  |  | owner=default |
| 15920 | 2026-08-17T23:27:26.830Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=80bcfafc732469b0f9a6ca003bf96912e74454adc53c5940ca49acebf908a067 |
| 15921 | 2026-08-17T23:27:27.067Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 15922 | 2026-08-17T23:29:20.561Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 15923 | 2026-08-17T23:29:20.824Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:1a9b573680690d76 | passed | bd70239045f4989dd01ee385082f3ff93c00f4f3aacec9da062efc6dde58e714 | False | 6920 | 0 |
| check:0650d77ec561a074 | passed | 57c6017860a3d5e87c1d7244433880812c4a441e81e7f87c8ef0dff97d18f2c3 | False | 827 | 0 |
| verify:tests | passed | 80bcfafc732469b0f9a6ca003bf96912e74454adc53c5940ca49acebf908a067 | False | 9983 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| c6e180efd7b54427ab83e330a7f5942a | accepted | bc17700e475ce74c96a9547117aade58823f0811 | 0b718bb9f58e1897308e1335d33ed8a0b7d22e76f96be233d22c673f6ac545e8 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `32`
- Chain head: `c8e2d004be59b322a8575217778b20f20db9e90ef313adc5d5982e703570011e`
