# Orchestration Wave 1

- Run: `714feb67173f45a4821b2e15aa887bc7`
- Wave: `d343dc4a80dd46c09fc8ad3546452ce5`
- Objective: Post-activation L3 live canary only. Create one fresh content-free ChatWeb-controlled diagnostic RUN under the current activated runtime and execute exactly npm run dev:status as the sole command/oracle. Do not modify source, do not clean/reset/revert, do not restart, commit, push, release, deploy, or invoke provider work. Preserve server-derived host correlation only; do not trust caller-supplied turn_id or trace_id. The purpose is to observe whether the activated attested_chatweb_transport_trace path binds this fresh ChatWeb turn and later receives exact controller usage. Missing usage must remain unknown_not_zero.
- Objective revision: `1`
- Objective SHA-256: `cab7f1a8dabac940dd3042fb8e16e47e5996816986d1f3ff7194370fa33251b9`
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
| 38037 | 2026-09-03T16:47:25.556Z | run_started |  | PREFLIGHT |  |
| 38038 | 2026-09-03T16:47:26.023Z | observation_span_recorded |  |  |  |
| 38039 | 2026-09-03T16:47:27.063Z | observation_span_recorded |  |  |  |
| 38040 | 2026-09-03T16:47:27.387Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 38041 | 2026-09-03T16:47:27.626Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 38042 | 2026-09-03T16:47:27.842Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 38043 | 2026-09-03T16:47:28.252Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 38044 | 2026-09-03T16:47:28.507Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 38045 | 2026-09-03T16:47:28.700Z | state_transition | READY | ROUTED | reason=route_selected |
| 38046 | 2026-09-03T16:47:28.939Z | observation_span_recorded |  |  |  |
| 38047 | 2026-09-03T16:47:29.942Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=9985e1a71b8f4341b446dede3229ee13 |
| 38048 | 2026-09-03T16:47:30.228Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 38049 | 2026-09-03T16:47:31.421Z | observation_span_recorded |  |  |  |
| 38050 | 2026-09-03T16:47:31.793Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=9985e1a71b8f4341b446dede3229ee13 |
| 38051 | 2026-09-03T16:47:32.000Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 38052 | 2026-09-03T16:47:32.880Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:385f51573288f6e6; input_fingerprint=24d756ae8d301c381ca061a5c4ec7736d4f6bca7b8b42ec67f75e765ed5ac931 |
| 38053 | 2026-09-03T16:47:33.291Z | managed_process_admitted |  |  | owner=default |
| 38054 | 2026-09-03T16:47:33.675Z | managed_process_started |  |  | owner=default |
| 38055 | 2026-09-03T16:47:34.376Z | managed_process_terminal |  |  | owner=default |
| 38056 | 2026-09-03T16:47:34.766Z | proof_recorded |  |  | stage_id=check:385f51573288f6e6; status=passed; cache_hit=False; input_fingerprint=24d756ae8d301c381ca061a5c4ec7736d4f6bca7b8b42ec67f75e765ed5ac931 |
| 38057 | 2026-09-03T16:47:35.008Z | observation_span_recorded |  |  |  |
| 38058 | 2026-09-03T16:47:35.241Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 38112 | 2026-09-03T16:48:12.718Z | quality_outcome_recorded |  |  |  |
| 38113 | 2026-09-03T16:48:12.904Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 38114 | 2026-09-03T16:48:13.412Z | observation_span_recorded |  |  |  |
| 38115 | 2026-09-03T16:48:13.640Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:385f51573288f6e6 | passed | 24d756ae8d301c381ca061a5c4ec7736d4f6bca7b8b42ec67f75e765ed5ac931 | False | 1488 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| ee7321d9a6a944fea700f41b98da6ef3 | accepted | 80aceb583202ad381c25687969fb48adbf74622c | f2c79fb6129ed25aa26ad9e24affc0833474174c41dd7ac0f0d97658468a0430 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `1da02f6b44d899a677ad1807b3ab3a86cde96c21c18554ce570cac68625dc420`
