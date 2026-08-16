# Orchestration Wave 1

- Run: `222d50dd27a745c2bc6edee3a9204d84`
- Wave: `6de5d7ab76cf4b08a840d8abd21c3989`
- Objective: Move the Recovery Tunnel configuration UI out of Settings and into Connections, directly alongside the primary Tunnel ID in the OpenAI Tunnel identity panel. Preserve existing Recovery Tunnel backend, telemetry, header status, duplicate-ID validation, save behavior, and OpenAI tunnel management link. Simplify the Connections UX so primary and recovery tunnel IDs are configured together; remove the standalone Recovery Tunnel card from Settings. Preserve unrelated concurrent work.
- Mode: `mcp_only`
- Base HEAD: `415cb658f43cbd1d2456f65bf5649ed52b87ab25`
- Worktree fingerprint: `a4c28c4edd9321872b82a75c50977566c7cb4468f4f4c2894e005b27918df388`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 6996 | 2026-08-16T10:26:22.841Z | run_started |  | PREFLIGHT |  |
| 6997 | 2026-08-16T10:26:25.617Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 6998 | 2026-08-16T10:27:00.676Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 6999 | 2026-08-16T10:27:00.795Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 7000 | 2026-08-16T10:27:00.919Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 7001 | 2026-08-16T10:27:01.032Z | state_transition | READY | ROUTED | reason=route_selected |
| 7002 | 2026-08-16T10:27:01.416Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=abaedda84d544c8db3d087113ee66cd5 |
| 7003 | 2026-08-16T10:27:01.531Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 7004 | 2026-08-16T10:27:02.000Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=abaedda84d544c8db3d087113ee66cd5 |
| 7005 | 2026-08-16T10:27:02.100Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 7006 | 2026-08-16T10:27:02.402Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:9f3f83d6b46d2388; input_fingerprint=9b3869a8631193a7434b4a2fdd980921ce51bd8395e9c50758f9a22955b54ca7 |
| 7007 | 2026-08-16T10:27:02.600Z | managed_process_admitted |  |  | owner=default |
| 7008 | 2026-08-16T10:27:02.813Z | managed_process_started |  |  | owner=default |
| 7009 | 2026-08-16T10:27:03.526Z | managed_process_terminal |  |  | owner=default |
| 7010 | 2026-08-16T10:27:03.719Z | proof_recorded |  |  | stage_id=check:9f3f83d6b46d2388; status=passed; cache_hit=False; input_fingerprint=9b3869a8631193a7434b4a2fdd980921ce51bd8395e9c50758f9a22955b54ca7 |
| 7011 | 2026-08-16T10:27:03.859Z | proof_cache_miss |  |  | reason=cold; stage_id=check:3d35ce374badfbf9; input_fingerprint=cb0dddd99ccfc8d346893170eb46724b94ae8cf77ecc2ee405def8810c8358fc |
| 7012 | 2026-08-16T10:27:04.109Z | managed_process_admitted |  |  | owner=default |
| 7013 | 2026-08-16T10:27:04.368Z | managed_process_started |  |  | owner=default |
| 7014 | 2026-08-16T10:27:05.075Z | managed_process_terminal |  |  | owner=default |
| 7015 | 2026-08-16T10:27:05.276Z | proof_recorded |  |  | stage_id=check:3d35ce374badfbf9; status=passed; cache_hit=False; input_fingerprint=cb0dddd99ccfc8d346893170eb46724b94ae8cf77ecc2ee405def8810c8358fc |
| 7016 | 2026-08-16T10:27:05.373Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=ba224fc387b0901980f53a9f27dde24bed6c906dd03b664b80c4b8632af1cf6b |
| 7017 | 2026-08-16T10:27:05.596Z | managed_process_admitted |  |  | owner=default |
| 7018 | 2026-08-16T10:27:05.796Z | managed_process_started |  |  | owner=default |
| 7019 | 2026-08-16T10:27:06.576Z | managed_process_terminal |  |  | owner=default |
| 7020 | 2026-08-16T10:27:06.776Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=ba224fc387b0901980f53a9f27dde24bed6c906dd03b664b80c4b8632af1cf6b |
| 7021 | 2026-08-16T10:27:07.465Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 7022 | 2026-08-16T10:27:22.684Z | managed_process_admitted |  |  | owner=default |
| 7023 | 2026-08-16T10:27:22.887Z | managed_process_started |  |  | owner=default |
| 7024 | 2026-08-16T10:27:23.204Z | managed_process_terminal |  |  | owner=default |
| 7025 | 2026-08-16T10:29:50.244Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 7026 | 2026-08-16T10:29:50.555Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:9f3f83d6b46d2388 | passed | 9b3869a8631193a7434b4a2fdd980921ce51bd8395e9c50758f9a22955b54ca7 | False | 1152 | 0 |
| check:3d35ce374badfbf9 | passed | cb0dddd99ccfc8d346893170eb46724b94ae8cf77ecc2ee405def8810c8358fc | False | 1203 | 0 |
| verify:tests | passed | ba224fc387b0901980f53a9f27dde24bed6c906dd03b664b80c4b8632af1cf6b | False | 1219 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 1a1bad8c6b504d91849599b020bd033c | accepted | 415cb658f43cbd1d2456f65bf5649ed52b87ab25 | aa6491cbf818a13b71cf230420e45881672e7cb0845e9290f461d17b4c674208 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `31`
- Chain head: `10c0f256f43c8cde79dff0d928ec5b5863d7ea3a388889bdb47e46aa56ef04d8`
