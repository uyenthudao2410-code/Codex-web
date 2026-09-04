# Orchestration Wave 1

- Run: `801d8e34171249fda53ec2851f0ab1b6`
- Wave: `21dc409278b1423582356dc17603b7c7`
- Objective: G2-P1 provenance closure only for the exact existing CANARY_TOKEN_BUDGET=4096 packet. Adopt, without changing source bytes, exactly scripts/execution-hub-provider-canary.js at SHA-256 a0c7e61c0b9a5dccff7b969cbdbf7320c39b5282889adac7c4a5aa0804eeb022 and tests/execution-hub-provider-canary.test.js at SHA-256 f4a4fbc8351b1e5b7d02becb00e4e380a2705547d918cd06d7d3fe22d9d33812. The source behavior is that the canary request carries token_budget=CANARY_TOKEN_BUDGET where CANARY_TOKEN_BUDGET=4096, and the focused test asserts dispatchedBody.token_budget equals that exported constant. Preserve all concurrent WIP and all paths outside this two-file scope. Do not run a live provider canary. No source write, bulk adoption, SQLite access, process/lease manipulation, reconcile, restart, reset, restore, clean, rebase, commit, push, tag, release, publish or deploy. ChatWeb Sol remains controller and final-acceptance owner.
- Objective revision: `1`
- Objective SHA-256: `44b0f0c6f9dcc7c1602ed16fcc829d3bad70f034d69a0df80c39a69157e535fb`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `6e9a91755453f579b1b44200b78043fb1794a60c0b9770d93484d0c428df5dd2`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 37817 | 2026-09-03T16:25:56.888Z | run_started |  | PREFLIGHT |  |
| 37818 | 2026-09-03T16:25:57.310Z | observation_span_recorded |  |  |  |
| 37819 | 2026-09-03T16:25:58.157Z | observation_span_recorded |  |  |  |
| 37820 | 2026-09-03T16:25:58.339Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 37821 | 2026-09-03T16:25:58.763Z | managed_process_admitted |  |  | owner=default |
| 37822 | 2026-09-03T16:25:59.068Z | managed_process_started |  |  | owner=default |
| 37823 | 2026-09-03T16:25:59.484Z | managed_process_terminal |  |  | owner=default |
| 37824 | 2026-09-03T16:25:59.744Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 37825 | 2026-09-03T16:25:59.890Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 37826 | 2026-09-03T16:26:00.025Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 37827 | 2026-09-03T16:26:00.261Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 37828 | 2026-09-03T16:26:00.423Z | state_transition | READY | ROUTED | reason=route_selected |
| 37829 | 2026-09-03T16:26:00.657Z | observation_span_recorded |  |  |  |
| 37830 | 2026-09-03T16:26:01.710Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=755c24d937004bf28c7ba185e088772f |
| 37831 | 2026-09-03T16:26:01.926Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 37832 | 2026-09-03T16:26:02.770Z | existing_file_adoption_observed |  |  |  |
| 37833 | 2026-09-03T16:26:03.011Z | observation_span_recorded |  |  |  |
| 37834 | 2026-09-03T16:26:03.426Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=755c24d937004bf28c7ba185e088772f |
| 37835 | 2026-09-03T16:26:03.640Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 37836 | 2026-09-03T16:26:04.394Z | proof_cache_miss |  |  | reason=cold; stage_id=check:1fa185667f1dece9; input_fingerprint=92aeb54a6b0e544d34c3c50dc2c3629a49b6b000af47fda011a723847925e292 |
| 37837 | 2026-09-03T16:26:04.731Z | managed_process_admitted |  |  | owner=default |
| 37838 | 2026-09-03T16:26:05.101Z | managed_process_started |  |  | owner=default |
| 37839 | 2026-09-03T16:26:05.551Z | managed_process_terminal |  |  | owner=default |
| 37840 | 2026-09-03T16:26:05.981Z | proof_recorded |  |  | stage_id=check:1fa185667f1dece9; status=passed; cache_hit=False; input_fingerprint=92aeb54a6b0e544d34c3c50dc2c3629a49b6b000af47fda011a723847925e292 |
| 37841 | 2026-09-03T16:26:06.230Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=ab1ab2747dc17f4f931eff6b5aeb827cdc7b6a57ac0b79b8fd35d8a6a2116f01 |
| 37842 | 2026-09-03T16:26:06.598Z | managed_process_admitted |  |  | owner=default |
| 37843 | 2026-09-03T16:26:06.941Z | managed_process_started |  |  | owner=default |
| 37844 | 2026-09-03T16:26:07.381Z | managed_process_terminal |  |  | owner=default |
| 37845 | 2026-09-03T16:26:08.212Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=ab1ab2747dc17f4f931eff6b5aeb827cdc7b6a57ac0b79b8fd35d8a6a2116f01 |
| 37846 | 2026-09-03T16:26:08.430Z | observation_span_recorded |  |  |  |
| 37847 | 2026-09-03T16:26:08.656Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 37852 | 2026-09-03T16:27:16.444Z | quality_outcome_recorded |  |  |  |
| 37853 | 2026-09-03T16:27:16.632Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 37854 | 2026-09-03T16:27:16.939Z | observation_span_recorded |  |  |  |
| 37855 | 2026-09-03T16:27:17.209Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:1fa185667f1dece9 | passed | 92aeb54a6b0e544d34c3c50dc2c3629a49b6b000af47fda011a723847925e292 | False | 1212 | 0 |
| verify:tests | passed | ab1ab2747dc17f4f931eff6b5aeb827cdc7b6a57ac0b79b8fd35d8a6a2116f01 | False | 1655 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| f6a759abc6944d9d9f1822645dbe3a73 | accepted | 80aceb583202ad381c25687969fb48adbf74622c | c3f639adeb54f5e07ebd0c6f4d189938d6f32015a04cba75888b623916ba6d68 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `683d76e27424cb49e9fd4b2e7f988c522c308556742b859849a9f01a66c44dcc`
